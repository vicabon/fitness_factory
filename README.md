# 健身工廠課表查詢 (Fitness Factory Schedule)

爬取健身工廠雙北地區（北一區：台北市、北二區：新北市）全天團體課程資料，並自動產生響應式靜態網頁（支援 GitHub Pages 部署）。

提供課程名稱篩選、廠館勾選、老師搜尋、一鍵新增至 Google 行事曆等功能。

---

## 🌟 主要功能

1. **雙北全天課表爬取**：
   - **北一區（台北市）**：台北萬隆、台北長春、台北安和、台北石牌、台北信義、台北健康、台北中山北。
   - **北二區（新北市）**：新北新店、新北板橋、新北汐科、新北林口、新北蘆洲、新北龍安、新北雙和、新北中和、新北新埔、新北永和、新北汐止、新北土城、新北七張、新北新莊、新北淡水、新北三重。
   - 涵蓋未來 4 週的全天開課時段。
2. **多維度快速篩選**：
   - **課程標籤**：可按課程名稱多選/單選，並提供「全選 / 全消」快速按鈕。
   - **指定廠館**：支援依區域與廠館勾選，並預設常用廠館。
   - **授課老師搜尋**：輸入文字即時比對（支援逗號多位老師搜尋）。
3. **代課標記與過濾**：
   - 自動辨識並標註「代課」課程。
   - 自動過濾停課、暫停、師資考核等非正常上課資訊。
4. **一鍵加入 Google 行事曆**：
   - 桌機表格與手機卡片皆提供「📅 加入行事曆」按鈕。
   - 採用 Google Calendar 官方推薦事件範本格式（`https://calendar.google.com/calendar/r/eventedit?action=TEMPLATE`），自動帶入課程名稱、老師、廠館位置與課程時間。
5. **響應式排版 (RWD)**：
   - **桌機版**：清楚的時間分組折疊表格，附帶滑鼠懸停星期高亮與行事曆欄位。
   - **手機版**：專為行動裝置最佳化的卡片式佈局，方便單手瀏覽與點擊。
6. **自動化更新**：
   - 內建 GitHub Actions 定時每週更新，亦可在網頁端點擊「更新課表」輸入 Token 手動觸發。

---

## 🛠️ 技術架構

- **Python 3**：
  - `requests`：模擬請求抓取健身工廠 API 課表。
  - `beautifulsoup4`：解析 HTML 課表格線與日期欄位。
- **HTML / CSS / Vanilla JavaScript**：
  - 無外部重型前端框架依賴，載入速度極快。
- **GitHub Actions & GitHub Pages**：
  - 排程自動化爬取、產生 `index.html` 並推送發布。

---

## 🚀 本地使用方式

### 1. 安裝環境與相依套件

確保已安裝 Python 3.8+：

```bash
pip install requests beautifulsoup4
```

### 2. 抓取課表並產出網頁

執行 `generate.py`：

```bash
python generate.py
```
> 爬蟲會遍歷雙北各廠館未來 4 週資料，抓取約需 2~3 分鐘。產出的 `index.html` 即為最新課表靜態網頁。

### 3. 本地預覽

直接以瀏覽器開啟 `index.html`，或使用 Python 本地伺服器開啟：

```bash
python -m http.server 8000
```
瀏覽 `http://localhost:8000` 即可預覽。

---

## 🔄 GitHub Actions 自動更新

本專案於 `.github/workflows/update-schedule.yml` 設定了自動化流程：
- **排程更新**：每週日 06:00 (台灣時間 UTC+8) 自動執行爬蟲更新 `index.html` 並 commit push。
- **手動更新 (Web UI)**：
  點擊網頁右上角的「更新課表」按鈕，輸入具備 `workflow` / `actions:write` 權限的 GitHub Personal Access Token 即可直接觸發遠端爬蟲。
