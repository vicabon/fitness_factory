#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健身工廠課表爬蟲
抓取北一區(台北市)和北二區(新北市)當月課程資料
條件：早上到18:00開課，代課課程往後一/兩週同廠館同時間顯示
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, date, timedelta
import time


BASE = 'https://www.fitnessfactory.com.tw'
TW_BASE = f'{BASE}/tw'

# 北一區 = 台北市分店，北二區 = 新北市分店
REGIONS = {
    '北一區': {
        'city': '台北市',
        'stores': ['台北萬隆', '台北長春', '台北安和', '台北石牌',
                   '台北信義', '台北健康', '台北中山北'],
    },
    '北二區': {
        'city': '新北市',
        'stores': ['新北新店', '新北板橋', '新北汐科', '新北林口',
                   '新北蘆洲', '新北龍安', '新北雙和', '新北中和',
                   '新北新埔', '新北永和', '新北汐止', '新北土城',
                   '新北七張', '新北新莊', '新北淡水', '新北三重'],
    },
}

COURSE_KEYWORDS = {
    '瑜珈': ['瑜珈', '瑜伽', 'yoga', 'Yoga'],
    '飛輪': ['飛輪', 'cycle', 'Cycle', 'spinning', 'E-Cycle', 'EOXi'],
    '舞蹈': ['舞蹈', '舞', 'ZUMBA', 'Zumba', '爵士', '嘻哈', '放克',
             '有氧', '台客', '懷舊', '迪斯可'],
    '芭蕾': ['芭蕾', 'ballet', 'Ballet', '蕾之律', 'barre'],
}

WEEKDAY_ORDER = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
WEEKDAY_EN = {0: '星期一', 1: '星期二', 2: '星期三', 3: '星期四',
              4: '星期五', 5: '星期六', 6: '星期日'}


def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'),
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'application/json, text/html, */*',
        'X-Requested-With': 'XMLHttpRequest',
    })

    resp = session.get(f'{TW_BASE}/course?page=schedule', timeout=15)
    soup = BeautifulSoup(resp.text, 'html.parser')
    csrf_meta = soup.find('meta', attrs={'name': 'csrf-token'})
    if csrf_meta:
        session.headers.update({'X-CSRF-TOKEN': csrf_meta['content']})

    # Extract available week dates from page
    dr = re.search(r"data-range='(\[[^\]]+\])'", resp.text)
    if dr:
        dates = json.loads(dr.group(1).replace('&quot;', '"'))
    else:
        today = date.today()
        mon = today - timedelta(days=today.weekday())
        dates = [(mon + timedelta(weeks=i)).strftime('%Y-%m-%d') for i in range(4)]

    session.headers.update({'Referer': f'{TW_BASE}/course?page=schedule'})
    return session, dates


SUB_MARKERS = re.compile(r'[🔺▲★✦]')

def is_substitute(course_name):
    return bool(SUB_MARKERS.search(course_name)) or '代課' in course_name

def clean_course_name(course_name):
    """Remove substitute markers from course name."""
    return SUB_MARKERS.sub('', course_name).strip()


def parse_start_time(time_str):
    """Return (hour, minute) of the start time"""
    m = re.match(r'(\d{1,2}):(\d{2})', time_str.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return 99, 0


def is_valid_time(time_str):
    """True if course starts at or before 18:00 exactly"""
    h, m = parse_start_time(time_str)
    return h < 18 or (h == 18 and m == 0)


def matches_category(course_name, selected_categories):
    if not selected_categories:
        return True
    name_lower = course_name.lower()
    for cat in selected_categories:
        for kw in COURSE_KEYWORDS.get(cat, [cat]):
            if kw.lower() in name_lower:
                return True
    return False


def get_course_category(course_name):
    for cat, keywords in COURSE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in course_name.lower():
                return cat
    return '其他'


def get_region_for_store(store_name):
    for region, info in REGIONS.items():
        if store_name in info['stores']:
            return region
    return '未知'


def fetch_schedule_for_store(session, store_name, week_start_date):
    """
    Fetch schedule for one store for the week starting at week_start_date.
    Returns list of course dicts with actual dates.
    """
    try:
        r = session.get(f'{TW_BASE}/course/ajax/filterSchedule', params={
            'page': 'schedule',
            'store': store_name,
            'cate': '0',
            'class': '0',
            'teacher': '0',
            'room': '0',
            'date': week_start_date,
        }, timeout=15)

        if r.status_code != 200:
            return []

        data = r.json()
        schedule_html = data.get('scheduleView', '')
        date_html = data.get('dateView', '')

        if not schedule_html:
            return []

        # Parse date headers to get column -> (day_num, weekday, actual_date)
        date_soup = BeautifulSoup(date_html, 'html.parser')
        day_cols = []

        # Parse year/month from bkDateYear/bkDateMonth
        year_el = date_soup.find(class_='bkDateYear')
        month_el = date_soup.find(class_='bkDateMonth')
        # Fallback from week_start_date
        ref_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
        year = int(year_el.text.strip()) if year_el else ref_date.year
        # Handle ROC year (民國年 = 1911 + ROC)
        if year < 200:
            year += 1911
        month = int(month_el.text.strip()) if month_el else ref_date.month

        for th in date_soup.find_all(class_='th'):
            date_box = th.find(class_='date-box')
            if date_box:
                d_el = date_box.find(class_='date')
                w_el = date_box.find(class_='week')
                if d_el and w_el:
                    day_num = int(d_el.text.strip())
                    weekday = w_el.text.strip()
                    try:
                        actual_date = date(year, month, day_num)
                    except ValueError:
                        # Month overflow: e.g. day 1 in next month
                        if day_num < 15:
                            nm = month % 12 + 1
                            ny = year + (1 if month == 12 else 0)
                            actual_date = date(ny, nm, day_num)
                        else:
                            pm = (month - 2) % 12 + 1
                            py = year - (1 if month == 1 else 0)
                            actual_date = date(py, pm, day_num)
                    day_cols.append({
                        'day': day_num,
                        'weekday': weekday,
                        'actual_date': actual_date,
                    })

        # Parse schedule rows
        schedule_soup = BeautifulSoup(schedule_html, 'html.parser')
        courses = []

        for tr in schedule_soup.find_all('div', class_='tr'):
            tds = tr.find_all('div', class_='td')
            for col_idx, td in enumerate(tds):
                if col_idx >= len(day_cols):
                    continue
                col = day_cols[col_idx]

                for course_box in td.find_all('div', class_='course-box'):
                    name_el = course_box.find(class_='name')
                    time_el = course_box.find(class_='time')
                    teacher_el = course_box.find(class_='teacher')

                    if not (name_el and time_el):
                        continue

                    raw_name = name_el.text.strip()
                    course_name = clean_course_name(raw_name)
                    course_time = time_el.text.strip()
                    teacher_spans = teacher_el.find_all('span') if teacher_el else []
                    teacher = ' / '.join(
                        s.text.strip() for s in teacher_spans if s.text.strip()
                    )

                    courses.append({
                        'store': store_name,
                        'region': get_region_for_store(store_name),
                        'weekday': col['weekday'],
                        'actual_date': col['actual_date'],
                        'day': col['day'],
                        'week_start': week_start_date,
                        'course_name': course_name,
                        'course_time': course_time,
                        'teacher': teacher,
                        'is_substitute': is_substitute(raw_name),
                        'category': get_course_category(course_name),
                    })

        return courses

    except Exception as e:
        print(f"  ERROR {store_name} {week_start_date}: {e}", file=sys.stderr)
        return []


def fetch_all_courses(selected_regions=None, selected_categories=None,
                      selected_stores=None, selected_teachers=None,
                      progress_callback=None):
    """
    Fetch all courses for selected regions/categories.
    Returns (courses_list, dates_list)
    """
    print("Initializing session...", file=sys.stderr)
    session, dates = create_session()
    print(f"Available week dates: {dates}", file=sys.stderr)

    # Build store list
    if selected_regions:
        base_stores = []
        for region in selected_regions:
            base_stores.extend(REGIONS.get(region, {}).get('stores', []))
    else:
        base_stores = [s for r in REGIONS.values() for s in r['stores']]

    if selected_stores:
        stores_to_query = [s for s in base_stores if s in selected_stores]
    else:
        stores_to_query = base_stores

    total = len(stores_to_query) * len(dates)
    done = 0
    print(f"Querying {len(stores_to_query)} stores × {len(dates)} weeks = {total} requests...", file=sys.stderr)

    all_raw = []
    for store in stores_to_query:
        for date_str in dates:
            done += 1
            if progress_callback:
                progress_callback(done, total, store, date_str)
            print(f"  [{done}/{total}] {store} {date_str}", file=sys.stderr)
            courses = fetch_schedule_for_store(session, store, date_str)
            all_raw.extend(courses)
            time.sleep(0.25)

    # Apply filters and build final list
    filtered = []
    seen = set()

    for c in all_raw:
        # Skip duplicate (same store+date+time+course)
        dedup_key = (c['store'], c['actual_date'], c['course_time'], c['course_name'])
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Time filter: start <= 18:00
        if not is_valid_time(c['course_time']):
            continue

        # Category filter
        if not matches_category(c['course_name'], selected_categories):
            continue

        # Teacher filter
        if selected_teachers:
            if not any(t.lower() in c['teacher'].lower() for t in selected_teachers):
                continue

        filtered.append(c)

    print(f"Total after filtering: {len(filtered)}", file=sys.stderr)
    return filtered, dates


if __name__ == '__main__':
    courses, dates = fetch_all_courses(
        selected_regions=['北一區'],
        selected_categories=['瑜珈', '飛輪'],
    )
    print(f"\nFound {len(courses)} courses")
    for c in sorted(courses, key=lambda x: (x['weekday'], x['store'], x['course_time']))[:15]:
        sub_info = f" [代課→{c['sub_forward_dates']}]" if c['is_substitute'] else ""
        print(f"  {c['weekday']} {c['store']} {c['course_time']} {c['course_name']} / {c['teacher']}{sub_info}")
