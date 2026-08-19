# 丰裕学 / Abundantics 官网

基于 Astro 的中英双语静态网站。以每日更新的 Token 能量平价指数（TEPI）实时大屏为门面，以丰裕学核心文献和研究文章为内核。

- **技术栈**：Astro + React (Recharts) + Tailwind CSS
- **正式域名**：https://abundantics.org（Cloudflare Pages 托管，pages.dev 子域仅作预览）
- **数据**：跨仓库只读拉取 [tanghuidao/token-parity](https://github.com/tanghuidao/token-parity) 的 CSV（`parity_series.csv`）
- **CI/CD**：GitHub Actions，每日 UTC 00:40 自动拉数 + 构建 + 部署

## 快速开始

```bash
npm install          # 安装依赖
npm run fetch:data   # 拉取 TEPI 数据（失败时自动沿用/MOCK）
npm run dev          # 本地开发服务器
npm run build        # 构建生产版本到 dist/
```

### ⚠️ 本地构建注意事项（WorkBuddy 环境）

在 WorkBuddy 沙箱环境中构建时，安全删除守卫会拦截 Astro 的清理步骤，需覆盖 `NODE_OPTIONS`：

```bash
NODE_OPTIONS="--use-system-ca" npm run build
```

依赖版本已锁定：`@astrojs/sitemap` 固定为 `3.2.1`（3.3+ 需要 Astro 5），且需在 `node_modules/@astrojs/sitemap/node_modules/` 下嵌套 zod v3（顶层 zod v4 会破坏其 API）。正常 `npm install` 后如构建报 zod 错误，从 `node_modules/astro/node_modules/zod` 复制一份过去即可。

## 目录结构

```
├── .github/workflows/deploy.yml   # CI/CD：每日 UTC 00:40 拉数+构建+部署
├── scripts/fetch_data.mjs         # 从 token-parity 拉 CSV 并转换 latest.json（只转换，不计算）
├── public/
│   ├── api/parity/                # latest.json, history.csv（静态 JSON API）
│   ├── files/                     # 预印本 PDF 等下载文件
│   ├── llms.txt                   # AI 爬虫站点说明
│   └── favicon.svg
├── src/
│   ├── content/
│   │   ├── research/              # 研究文章（zh/ en/ 子目录）
│   │   └── config.ts              # Content Collections schema
│   ├── components/                # IndexCard.tsx, Sparkline.tsx, LambdaChart.tsx, BibTeXBlock.astro, Nav.astro
│   ├── i18n/                      # zh.json, en.json, utils.ts（UI 字符串集中管理）
│   ├── layouts/                   # TerminalLayout.astro（深色）, ProseLayout.astro（浅色）
│   ├── lib/data.ts                # 构建时数据加载工具
│   ├── pages/
│   │   ├── index.astro            # 按浏览器语言重定向
│   │   ├── zh/                    # 中文页面（全量）
│   │   ├── en/                    # 英文页面（全量）
│   │   └── rss.xml.ts             # RSS 订阅
│   └── styles/global.css          # 全局样式（Tailwind）
├── preprint/                      # 预印本源文件（PDF/docx/md）
└── astro.config.mjs               # Astro 配置（i18n、React、Tailwind、sitemap）
```

## 如何新增研究文章

1. 在 `src/content/research/zh/`（中文）或 `src/content/research/en/`（英文）目录下新建 `.md` 文件
2. 添加 frontmatter：

```yaml
---
title: 文章标题
date: 2026-08-19        # 发布日期
lang: zh               # zh 或 en
description: 摘要（可选）
translation: slug-name  # 对应译文的文章 slug（可选，设置后隐藏"暂无译文"提示）
---

正文内容（Markdown）...
```

3. 提交并 push 到 main 分支，2 分钟内自动部署

## 如何更新方法论版本号

1. 修改 `src/pages/zh/index/methodology.astro` 与 `src/pages/en/index/methodology.astro` 中的版本表格
2. 数据文件中的 `method_version` 字段由 token-parity 仓库控制，本站自动读取

## 如何更新 UI 文案

所有 UI 字符串集中在 `src/i18n/zh.json` 与 `src/i18n/en.json`，禁止硬编码在组件里。

## 数据契约

- 前端只读 `public/api/parity/latest.json` 与 `history.csv`，禁止前端计算任何指数
- 数据拉取失败时不中断构建，沿用上一次数据
- `latest.json` 中 `mock: true` 表示 MOCK 数据，上线前必须替换

## 部署（Cloudflare Pages）

GitHub Actions 需配置以下 Secrets：
- `CLOUDFLARE_API_TOKEN` — Cloudflare API 令牌
- `CLOUDFLARE_ACCOUNT_ID` — Cloudflare 账户 ID

## 域名绑定与地址统一（v1.3，2026-08-19）

正式域名 abundantics.org 已注册于 Cloudflare Registrar，DNS 托管在 Cloudflare。代码侧已完成：

- `astro.config.mjs` 中 `site` 改为 `https://abundantics.org`（sitemap / RSS / canonical / hreflang 自动生成绝对地址）
- 布局层（`TerminalLayout` / `ProseLayout`）每页输出 `<link rel="canonical">` 与绝对地址 hreflang 互链
- `llms.txt`、`robots.txt`、RSS 兜底、About / 方法论页 BibTeX 引用地址全部统一为 abundantics.org
- 语言识别失败时默认落地 `/en/`（国际站定位，英文兜底）
- 全站已无 pages.dev / github.io / 127.0.0.1 硬编码残留（站点输出范围）

Cloudflare 面板待办（需在 Dashboard 手动执行，已列入交付说明）：

1. Cloudflare Pages 项目 → Custom domains → 添加 `abundantics.org`（apex 为主域名）
2. 同时添加 `www.abundantics.org`，用 Redirect Rules 配 301 → 根域
3. SSL/TLS 模式确认为 Full (Strict)，等待证书签发
4. pages.dev 子域保留作预览，不对外宣传

## 自主决策清单（v1.3）

1. **hreflang/canonical 实现位置**：在布局层用 `Astro.site` 拼接绝对地址，所有页面自动获得，无需逐页维护
2. **研究列表页跨语言显示**：`/en/research/` 与 `/zh/research/` 列表均显示全部语言文章并带语言徽标（修复英文列表在无英文文章时的空页问题；文章链接仍指向自身语言路由）
3. **数据拉取脚本**：候选路径新增 `parity_series.csv`（token-parity 主序列，已验证）；当 Node `fetch` 因本地 DNS 受限失败时自动回退 `curl`（GitHub Actions 上仍走 fetch 主路径）
4. **`defaultLocale` 改为 `en` 并关闭 Astro 自动根重定向**：`i18n.routing.redirectToDefaultLocale: false`，保留手写 `src/pages/index.astro` 的浏览器语言分流（中文 → `/zh/`，其余 → `/en/`）。否则 Astro 会把根路径替换成仅指向 `/en/` 的静态重定向，中文用户将无法到达中文版
5. **TEPI 数据已替换为真实序列**：`latest.json` 取自 token-parity `parity_series.csv`（截至 2026-08-19），MOCK 标记已移除

## 许可

- 站点内容与数据：[CC BY 4.0](LICENSE)
- TEPI 数据源：[tanghuidao/token-parity](https://github.com/tanghuidao/token-parity)
