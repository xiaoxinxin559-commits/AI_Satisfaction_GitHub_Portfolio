# 发布到 GitHub 与 GitHub Pages

本包尚未上传到任何 GitHub 仓库，因此没有实际在线作品 URL。请勿把本机文件路径或带占位符的网址当成已发布链接。

## 建议的仓库信息

仓库名：`ai-satisfaction-analysis-portfolio`

描述：`AI-assisted satisfaction analytics: human-in-the-loop decisions, data audits, leakage checks, interpretable models and an interactive portfolio. Synthetic data only.`

Topics：`data-analysis`、`ai-assisted-development`、`user-research`、`survey-analysis`、`data-quality`、`python`、`sql`、`portfolio`、`synthetic-data`。

不要加 `rag`、`mcp` 或 `multi-agent` 等尚未在本仓库实现的标签。

## 网页上传

在 GitHub 新建仓库。审核公开范围后，选择合适的可见性。解压作品包，将仓库目录内部的文件和文件夹上传到仓库根目录，不要只上传 ZIP，也不要再多套一层目录。

上传完成后确认根目录能看到 `README.md`，并能找到 `docs/index.html`。GitHub 官方支持通过网页上传文件和文件夹；若网页上传未保留空文件或隐藏文件，可通过 Git 补齐。[1]

## 启用作品页面

在仓库设置中打开 **Settings → Pages**，将发布来源设为 **Deploy from a branch**，选择 `main` 分支与 `/docs` 目录，保存并等待部署。部署成功后，从 Pages 设置页复制 GitHub 实际显示的站点地址。[2][3]

本项目 `docs/index.html` 是自包含文件，图像和数据已嵌入，没有必须配置的 API 地址。`docs/.nojekyll` 用来避免不必要的站点生成处理。

## 两种链接的用途

仓库链接供招聘方查看 README、方法说明、代码和测试；Pages 链接供招聘方直接浏览交互式作品。把最终实际生成的 Pages 地址填到仓库的 Website / About 栏；申请材料可以附其中一个或两个。

## 发布后检查

确认首页可打开；筛选器能改变演示样本量；字段搜索、角色筛选、排序与 CSV 导出可用；手机宽度无横向溢出；代码和所有图表都有“合成 / 重构”说明。页面中的静态模型图基于固定样本划分，不随探索筛选变化。

## 官方参考

[1] GitHub：上传文件。
https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository

[2] GitHub：配置 Pages 发布源。
https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

[3] GitHub：创建 Pages 站点。
https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
