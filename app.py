import gradio as gr
import lightkurve as lk
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil

SAVE_DIR = "discovered_candidates"
os.makedirs(SAVE_DIR, exist_ok=True)
current_run_data = {}

def search_and_analyze_planet(tic_id, min_period, max_period):
    global current_run_data
    try:
        tic_str = f"TIC {tic_id.strip().replace('TIC', '').replace('tic', '')}"
        search_res = lk.search_lightcurve(tic_str, mission="TESS")
        if len(search_res) == 0:
            return f"❌ 錯誤：在 NASA TESS 資料庫中找不到 {tic_str}。", None, gr.update(interactive=False)

        lc_collection = search_res[:3].download_all()
        if lc_collection is None or len(lc_collection) == 0:
            return f"❌ 錯誤：無法下載 {tic_str} 的數據。", None, gr.update(interactive=False)

        lc = lc_collection.stitch()
        lc_clean = lc.remove_nans().remove_outliers(sigma=5.0)
        lc_flat = lc_clean.flatten(window_length=101)

        period_grid = np.linspace(float(min_period), float(max_period), 3000)
        bls_model = lc_flat.to_periodogram(method="bls", period=period_grid)

        best_period = bls_model.period_at_max_power
        best_t0 = bls_model.transit_time_at_max_power
        best_depth = bls_model.depth_at_max_power
        sde = bls_model.max_power / np.median(bls_model.power)

        is_candidate = "⚠️ 待確認（雜訊或訊號微弱）"
        if sde > 6.0 and best_depth.value > 0.001:
            is_candidate = "🔥 高潛力候選行星！(SDE 強烈，凌日凹槽顯著)"

        fig, axes = plt.subplots(2, 1, figsize=(10, 8), dpi=120)
        bls_model.plot(ax=axes[0], color='teal')
        axes[0].axvline(best_period.value, color='red', linestyle='--', label=f'Best Period: {best_period.value:.4f} d')
        axes[0].set_title(f"BLS Periodogram - Signal Detection Efficiency (SDE): {sde:.2f}", fontsize=10)
        axes[0].legend()

        folded = lc_flat.fold(period=best_period, epoch_time=best_t0)
        folded.scatter(ax=axes[1], color='darkviolet', s=1.5, alpha=0.6)
        axes[1].set_title(f"Folded Light Curve at {best_period.value:.4f} days", fontsize=10)

        plt.tight_layout()
        plot_path = "temp_diagnostic_plot.png"
        plt.savefig(plot_path, dpi=120)
        plt.close(fig)

        current_run_data = {
            "tic_id": tic_str,
            "period": best_period.value,
            "t0": best_t0.value,
            "depth": best_depth.value,
            "sde": sde,
            "status": is_candidate,
            "img_path": plot_path
        }

        report_md = f"### 🌌 {tic_str} 盲搜成功報告：\n- **觀測數據區間**：已自動整合縫合並拉平 **{len(lc_collection)}** 個 TESS 觀測季度的數據。\n- **最強候選週期 (Period)**：`{best_period.value:.5f}` 天\n- **估算凌日深度 (Depth)**：`{best_depth.value * 100:.4f}%`\n- **訊號雜訊比指標 (SDE)**：`{sde:.2f}`\n- **系統自動篩選判定**：**{is_candidate}**"
        return report_md, plot_path, gr.update(interactive=True)
    except Exception as e:
        return f"❌ 系統運行出錯：{str(e)}", None, gr.update(interactive=False)

def save_candidate_to_local():
    global current_run_data
    if not current_run_data:
        return "⚠️ 尚未進行盲搜，無資料可儲存！"
    tic_id = current_run_data["tic_id"].replace(" ", "_")
    filepath = os.path.join(SAVE_DIR, f"{tic_id}_report.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"=== 系外行星盲搜報告 ({current_run_data['tic_id']}) ===\n")
        f.write(f"預測公轉週期 (Period): {current_run_data['period']:.6f} days\n")
        f.write(f"首次凌日時間 (t0): {current_run_data['t0']:.6f} BJD\n")
        f.write(f"凌日深度 (Depth): {current_run_data['depth']*100:.6f} %\n")
        f.write(f"訊號偵測效率 (SDE): {current_run_data['sde']:.2f}\n")
        f.write(f"自動判定狀態: {current_run_data['status']}\n")
    archive_img_path = os.path.join(SAVE_DIR, f"{tic_id}_plot.png")
    if os.path.exists(current_run_data["img_path"]):
        shutil.copy(current_run_data["img_path"], archive_img_path)
    return f"💾 成功！已存至本地 `{filepath}`！"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🪐 全自動系外行星盲搜系統 v2.0")
    with gr.Row():
        with gr.Column(scale=1):
            tic_input = gr.Textbox(label="TESS 星體編號 (TIC ID)", value="100100827")
            p_min = gr.Number(label="最小搜尋週期 (天)", value=0.5)
            p_max = gr.Number(label="最大搜尋週期 (天)", value=5.0)
            btn_search = gr.Button("🚀 開始 NASA 真實數據盲搜", variant="primary")
            btn_save = gr.Button("💾 儲存此高價值行星至本地", variant="secondary", interactive=False)
            save_status = gr.Textbox(label="儲存反饋", value="尚未儲存")
        with gr.Column(scale=2):
            output_report = gr.Markdown("等待指令...")
            output_image = gr.Image(label="BLS 分析圖表")
    btn_search.click(fn=search_and_analyze_planet, inputs=[tic_input, p_min, p_max], outputs=[output_report, output_image, btn_save])
    btn_save.click(fn=save_candidate_to_local, inputs=[], outputs=[save_status])

if __name__ == '__main__':
    demo.launch()