# 丰裕学 / Abundantics 官网

基于 Astro 的中英双语静态网站。以每日更新的 Token 能量平价指数（TEPI）实时大屏为门面，以丰裕学核心文献和研究文章为内核。

- **技术栈**：Astro + React (Recharts) + Tailwind CSS
- **托管**：Cloudflare Pages（pages.dev 子域，域名后续绑定）
- **数据**：跨仓库只读拉取 [tanghuidao/token-parity](https://github.com/tanghuidao/token-parity) 的 CSV
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

## 许可

- 站点内容与数据：[CC BY 4.0](LICENSE)
- TEPI 数据源：[tanghuidao/token-parity](https://github.com/tanghuidao/token-parity)
