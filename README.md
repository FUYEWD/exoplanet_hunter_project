# 🪐 Exoplanet Hunter Pipeline

這是一個自動化的系外行星特徵萃取專案，旨在處理 NASA TESS 任務的原始觀測數據，透過訊號處理與物理特徵工程，從極端雜訊中找出潛在的行星凌日訊號 (Transit Signal)。

## 🛠️ 核心技術與原理 (Tech Stack)
* **資料獲取**：串接 NASA `lightkurve` API 獲取恆星光變曲線 (Light Curve)。
* **訊號處理**：實作低頻去趨勢 (Flattening) 濾除感測器熱雜訊與環境漂移。
* **特徵工程**：運用相位摺疊 (Phase Folding) 與 BLS 演算法疊加微弱訊號，提升訊噪比 (SNR)。
* **自動化部署**：透過 Python 與 Streamlit 建立雲端可視化分析平台。

## 🚀 如何在本地端執行 (Quick Start)
1. 克隆此專案：`git clone https://github.com/FUYEWD/exoplanet_hunter_project.git`
2. 安裝相依套件：`pip install -r requirements.txt`
3. 啟動伺服器：`streamlit run app.py`
