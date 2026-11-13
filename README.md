# Northbean Coffee: Loyalty Intelligence Dashboard (Power BI)

![Cover](images/cover.png)

This is an end-to-end Power BI portfolio project. It covers loyalty analytics for **Northbean Coffee**, a fictional 28-store coffee chain in Portugal. All data is **synthetic**, built to behave like a real business: seasonality, member churn, reward redemptions and campaigns.

## What the report answers

| Page | Business question | Highlights |
|---|---|---|
| **Executive Overview** | Is the business growing, and how much of the growth comes from members? | KPI tiles with YoY deltas and sparklines, members vs guests vs prior year, channel mix, a store leaderboard, and a weekday × hour traffic heatmap |
| **Member Health & Retention** | Are we acquiring members and keeping them? | Active / new / returning / at-risk members, a monthly **cohort retention triangle**, acquisition channels, and member vs guest ticket size |
| **Points & Rewards Economy** | What does the programme cost, and how big is the liability? | Points issued vs redeemed, redemption rate, **outstanding points liability (€)**, reward ranking and reward P&L |
| **Campaign Performance** | Which challenges work? | Enrollment, completion and **spend uplift of participants vs non-participants** for each campaign and mechanic |

Each page also has a **headline sentence written by DAX** that summarises the current filter selection.

## Screenshots

| | |
|---|---|
| ![Overview](images/page_overview.png) | ![Members](images/page_members.png) |
| ![Rewards](images/page_rewards.png) | ![Campaigns](images/page_campaigns.png) |

![Model](images/model.png)

## Data model

- **Facts:** `Transactions` (518K rows), `Redemptions` (19K), `Campaign Enrollments` (8K)
- **Dimensions:** `Calendar` (a DAX date table, marked as the date table), `Stores`, `Members`, `Rewards`, `Campaigns`
- **Disconnected axis:** `Cohort Offset` (M+1 … M+12), used by the cohort matrix
- **Inactive relationship:** `Campaign Enrollments[CompletedDate]`, activated with `USERELATIONSHIP` for bonus points; new members by join date use `TREATAS`
- **No implicit measures.** All measures sit in one `_Measures` table, organised into display folders:
  - **Sales:** net sales, ticket, member share, food attach rate, traffic share
  - **Members:** active members, new members, returning % (vs the previous period of the same length), at-risk members (last visit 45–120 days ago), cohort retention
  - **Rewards:** points issued (purchases + campaign bonuses), redeemed, redemption rate, running liability, reward investment %
  - **Campaigns:** completion rate, plus spend per participant vs other active members during each campaign window
  - **KPI Cards:** a prior-year value, a delta, a ▲▼ label and a good/bad colour for every KPI (generated consistently)

## Design

A dark, coffee-inspired look built for quick reading. A sidebar menu moves between pages, filters for period, region and store format stay in sync across the report, and every KPI tile shows the value, the change vs last year and a monthly trend.

## How to open

1. Download the repository and put the `data` folder in `C:\Northbean\data\`
2. Open `Northbean.pbip` in Power BI Desktop
3. Click **Refresh**

---
Built by **Marko Knežević** · Northbean Coffee is a fictional brand.
