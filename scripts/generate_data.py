import numpy as np, pandas as pd, os, sys
rng = np.random.default_rng(2026)
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
START, END = pd.Timestamp('2025-01-01'), pd.Timestamp('2026-10-31')
days = pd.date_range(START, END, freq='D'); ND = len(days)

# ---------------- stores ----------------
stores = [
 ('Alfama','Lisbon','Lisbon Metro','Flagship','2019-04-12'),('Chiado','Lisbon','Lisbon Metro','Café','2020-02-03'),
 ('Belém','Lisbon','Lisbon Metro','Café','2021-06-21'),('Parque das Nações','Lisbon','Lisbon Metro','Café','2021-11-08'),
 ('Saldanha','Lisbon','Lisbon Metro','Kiosk','2022-03-14'),('Cais do Sodré','Lisbon','Lisbon Metro','Kiosk','2022-09-01'),
 ('Oeiras','Oeiras','Lisbon Metro','Drive-thru','2023-05-19'),('Cascais','Cascais','Lisbon Metro','Café','2023-07-07'),
 ('Sintra','Sintra','Lisbon Metro','Café','2025-06-02'),
 ('Ribeira','Porto','North','Flagship','2019-10-01'),('Boavista','Porto','North','Café','2020-09-15'),
 ('Bolhão','Porto','North','Kiosk','2021-04-30'),('Matosinhos','Matosinhos','North','Drive-thru','2022-06-10'),
 ('Gaia','Vila Nova de Gaia','North','Café','2023-02-20'),('Braga Centro','Braga','North','Café','2022-11-11'),
 ('Guimarães','Guimarães','North','Kiosk','2024-03-04'),('Aveiro','Aveiro','North','Café','2025-09-15'),
 ('Coimbra Baixa','Coimbra','Centre','Café','2021-01-18'),('Coimbra Universidade','Coimbra','Centre','Kiosk','2022-10-03'),
 ('Leiria','Leiria','Centre','Café','2023-09-25'),('Viseu','Viseu','Centre','Drive-thru','2024-05-13'),
 ('Faro Marina','Faro','Algarve','Café','2020-05-29'),('Lagos','Lagos','Algarve','Café','2021-05-14'),
 ('Albufeira','Albufeira','Algarve','Kiosk','2022-06-24'),('Portimão','Portimão','Algarve','Drive-thru','2023-04-07'),
 ('Tavira','Tavira','Algarve','Kiosk','2024-06-28'),('Évora','Évora','Centre','Café','2023-12-01'),
 ('Setúbal','Setúbal','Lisbon Metro','Drive-thru','2026-03-02'),
]
st = pd.DataFrame(stores, columns=['StoreName','City','Region','Format','OpenDate'])
st.insert(0,'StoreID', range(101, 101+len(st)))
st['StoreName'] = 'Northbean ' + st['StoreName']
st['OpenDate'] = pd.to_datetime(st['OpenDate'])
fmt_vol = {'Flagship':2.0,'Café':1.0,'Kiosk':0.7,'Drive-thru':1.15}
fmt_tkt = {'Flagship':1.12,'Café':1.0,'Kiosk':0.8,'Drive-thru':1.05}
st['vol'] = st['Format'].map(fmt_vol) * rng.uniform(0.8,1.25,len(st))
st.loc[st.Region=='Algarve','vol'] *= 0.9
st['SeatingCapacity'] = st['Format'].map({'Flagship':80,'Café':40,'Kiosk':0,'Drive-thru':12})

# seasonality
doy = days.dayofyear.values; dow = days.dayofweek.values; month = days.month.values
season = 1 + 0.12*np.cos(2*np.pi*(doy-15)/365)          # winter higher
season *= np.where(month==8, 0.86, 1.0)
dow_f = np.array([1.02,1.0,1.0,1.03,1.08,0.95,0.82])[dow]
trend = 1 + 0.10*(np.arange(ND)/365)                       # +10% / yr organic
algarve_summer = np.where(np.isin(month,[6,7,8,9]), 1.45, 0.85)
open_mask = (days.values[None,:] >= st['OpenDate'].values[:,None])
ramp = np.clip((days.values[None,:]-st['OpenDate'].values[:,None]).astype('timedelta64[D]').astype(int)/120,0.35,1)

# hourly profile (weekday / weekend)
hours = np.arange(7,22)
wk = np.array([5,11,9,6,5,8,7,5,6,5,4,3,2,1.5,1]);  we = np.array([2,5,8,9,8,8,7,6,6,5,5,4,3,2,1.5])
pw_wk, pw_we = wk/wk.sum(), we/we.sum()
def sample_hours(n, weekend):
    return rng.choice(hours, size=n, p=pw_we if weekend else pw_wk)

# ---------------- members ----------------
# monthly joins, with launch push in Jan 2025 + campaign spikes
months = pd.period_range('2023-06','2026-10',freq='M')
base = np.linspace(380, 820, len(months))
spike = {pd.Period('2025-01','M'):1.9, pd.Period('2025-05','M'):1.35, pd.Period('2025-10','M'):1.5,
         pd.Period('2026-02','M'):1.4, pd.Period('2026-09','M'):1.6}
joins = []
for i,m in enumerate(months):
    n = int(rng.poisson(base[i]*spike.get(m,1.0)*(0.55 if m < pd.Period('2025-01','M') else 1)))
    d0 = m.start_time; nd = m.days_in_month
    jd = d0 + pd.to_timedelta(rng.integers(0,nd,n),'D')
    joins.append(jd)
jd = pd.DatetimeIndex(np.concatenate(joins)).sort_values()
NM = len(jd)
mem = pd.DataFrame({'MemberID': np.arange(200001, 200001+NM), 'JoinDate': jd})
mem['JoinChannel'] = rng.choice(['App','In-store QR','Web','Referral'], NM, p=[.52,.30,.10,.08])
mem.loc[mem.JoinDate>='2025-10-01','JoinChannel'] = rng.choice(['App','In-store QR','Web','Referral'], (mem.JoinDate>='2025-10-01').sum(), p=[.62,.22,.06,.10])
mem['AgeBand'] = rng.choice(['18-24','25-34','35-44','45-54','55+'], NM, p=[.17,.34,.24,.15,.10])
# home store: only stores open at join (weighted by vol)
st_open = st['OpenDate'].values; st_vol = st['vol'].values
home = np.empty(NM, dtype=int)
for i,d in enumerate(mem['JoinDate'].values):
    ok = st_open <= d; w = st_vol*ok; home[i] = st['StoreID'].values[rng.choice(len(st), p=w/w.sum())]
mem['HomeStoreID'] = home
# behaviour: visit rate per month and churn
seg = rng.choice(['Daily ritual','Regular','Occasional','Lapsing'], NM, p=[.08,.27,.45,.20])
rate = np.select([seg=='Daily ritual',seg=='Regular',seg=='Occasional'], [rng.gamma(9,1.6,NM), rng.gamma(5,1.0,NM), rng.gamma(2,0.75,NM)], rng.gamma(1.5,0.6,NM))
monthly_churn = np.select([seg=='Daily ritual',seg=='Regular',seg=='Occasional'], [0.012,0.03,0.065], 0.16)
mem['_rate'] = rate*0.42; mem['_churn'] = monthly_churn
age_ticket = mem['AgeBand'].map({'18-24':0.88,'25-34':1.0,'35-44':1.08,'45-54':1.1,'55+':1.04}).values

rows = []
TID = 1
store_idx = {s:i for i,s in enumerate(st.StoreID)}
day_index = {d:i for i,d in enumerate(days)}
all_months = pd.period_range('2023-06','2026-10',freq='M')
print('members', NM)
for i in range(NM):
    j = mem.JoinDate.iat[i]; jm = j.to_period('M')
    alive = True
    for m in all_months:
        if m < jm: continue
        if m > jm and rng.random() < mem._churn.iat[i]:
            alive = False
        if not alive: break
        if m < pd.Period('2025-01','M'): continue
        d0 = max(m.start_time, j); d1 = m.end_time.normalize()
        if d0 > END: break
        span = (d1-d0).days+1
        lam = mem._rate.iat[i]*span/m.days_in_month
        n = rng.poisson(lam)
        if n == 0: continue
        dd = d0 + pd.to_timedelta(rng.integers(0,span,n),'D')
        rows.append((np.full(n, mem.MemberID.iat[i]), dd.values, np.full(n,i)))
mid = np.concatenate([r[0] for r in rows]); mdate = np.concatenate([r[1] for r in rows]); midx = np.concatenate([r[2] for r in rows])
NMT = len(mid)
# store for member visit: 72% home store, else other open store in region-ish
home_s = mem.HomeStoreID.values[midx]
other = st.StoreID.values[rng.choice(len(st), NMT, p=st_vol/st_vol.sum())]
mstore = np.where(rng.random(NMT) < 0.72, home_s, other)
# drop visits to stores not open yet
openat = st.set_index('StoreID').OpenDate.reindex(mstore).values
ok = mdate >= openat
mstore = np.where(ok, mstore, home_s)
mt = pd.DataFrame({'Date': mdate, 'StoreID': mstore, 'MemberID': mid, '_age': age_ticket[midx]})
print('member txns', len(mt))

# guests: per store/day poisson, declining guest share as program grows
guest_rows = []
for s_i, s in st.iterrows():
    lam = 16.5*s.vol*season*dow_f*trend*ramp[s_i]
    if s.Region=='Algarve': lam = lam*algarve_summer
    lam = lam*(1 - 0.22*np.arange(ND)/ND)       # guests convert into members
    n = rng.poisson(lam)*open_mask[s_i]
    guest_rows.append(pd.DataFrame({'Date': np.repeat(days.values, n), 'StoreID': s.StoreID}))
gt = pd.concat(guest_rows, ignore_index=True); gt['MemberID'] = np.nan; gt['_age'] = 1.0
print('guest txns', len(gt))
tx = pd.concat([mt, gt], ignore_index=True)
tx['Date'] = pd.to_datetime(tx['Date'])
tx = tx[(tx.Date>=START)&(tx.Date<=END)]
# member visits also follow seasonality: thin by season factor
sf = pd.Series(season*dow_f, index=days)
keep = rng.random(len(tx)) < (sf.reindex(tx.Date).values/ (season*dow_f).max())
keep |= tx.MemberID.isna().values
tx = tx[keep].sort_values(['Date','StoreID']).reset_index(drop=True)
N = len(tx)
weekend = tx.Date.dt.dayofweek.values >= 5
h = np.empty(N, dtype=int)
h[weekend] = sample_hours(weekend.sum(), True); h[~weekend] = sample_hours((~weekend).sum(), False)
tx['Hour'] = h
fmt = st.set_index('StoreID').Format.reindex(tx.StoreID).values
is_mem = tx.MemberID.notna().values
# channel
p_mem = [.58,.33,.09]; p_g = [.80,.10,.10]
ch = np.where(is_mem, rng.choice(3,N,p=p_mem), rng.choice(3,N,p=p_g))
ch = np.where(fmt=='Drive-thru', np.where(rng.random(N)<.75, 3, ch), ch)
tx['Channel'] = np.array(['In-store','Mobile order','Delivery','Drive-thru'])[ch]
# basket
items = 1 + rng.poisson(np.where(is_mem, 0.95, 0.7)) + (tx.Channel.values=='Delivery')
has_food = rng.random(N) < np.where(h<=10, .46, np.where(h<=14,.40,.27))*np.where(is_mem,1.12,1)
unit = rng.gamma(9, 0.36, N) * pd.Series(fmt).map(fmt_tkt).values * tx['_age'].values
price_up = np.where(tx.Date.values >= np.datetime64('2026-01-15'), 1.045, 1.0)
gross = (items*unit + has_food*rng.uniform(2.4,4.6,N)) * price_up
gross = np.round(gross, 2)
tx['Items'] = items + has_food.astype(int)
tx['HasFood'] = has_food.astype(int)
tx['GrossSales'] = gross
tx['Discount'] = 0.0
tx['PointsEarned'] = np.where(is_mem, np.floor(gross*10), 0).astype(int)

# ---------------- rewards / redemptions ----------------
rewards = pd.DataFrame([
 (1,'Free Espresso','Drink',600,0.38),(2,'Free Pastry','Food',900,0.70),(3,'Any Handcrafted Drink','Drink',1500,0.95),
 (4,'Breakfast Combo','Food',2500,2.10),(5,'250g Bag of Beans','Retail',4000,3.60),(6,'Northbean Tumbler','Merch',6000,5.20)],
 columns=['RewardID','RewardName','RewardCategory','PointsRequired','UnitCost'])
# tiers by trailing activity -> keep simple: tier by member segment and tenure
tier = np.where(seg=='Daily ritual','Gold', np.where(seg=='Regular', np.where(rng.random(NM)<.45,'Gold','Silver'), np.where(rng.random(NM)<.3,'Silver','Green')))
mem['Tier'] = tier
# redemption: walk member txns, redeem when balance allows (probability), attach to a txn as discount
tx['RedemptionID'] = 0
red_rows = []
mtx = tx[is_mem].copy(); mtx['_ix'] = mtx.index
mtx = mtx.sort_values(['MemberID','Date'])
pref = rng.choice(len(rewards), NM, p=[.34,.22,.24,.09,.07,.04])
RID = 1
bal = 0; cur = None
pts_req = rewards.PointsRequired.values; disc_val = np.array([3.0,3.4,5.2,8.9,14.5,22.0]); cost = rewards.UnitCost.values
mids = mtx.MemberID.values.astype(int); pts = mtx.PointsEarned.values; ixs = mtx._ix.values; dts = mtx.Date.values; sts = mtx.StoreID.values
red_ix=[]; red_m=[]; red_r=[]; red_d=[]; red_s=[]
mid2i = pd.Series(np.arange(NM), index=mem.MemberID.values)
prob_redeem = 0.42
for k in range(len(mids)):
    m = mids[k]
    if m != cur: cur = m; bal = int(rng.integers(0, 400)); pr = pref[mid2i[m]]
    if bal >= pts_req[pr] and rng.random() < prob_redeem:
        r = pr
    elif bal >= pts_req[0] and rng.random() < 0.08:
        r = 0
    else:
        r = -1
    if r >= 0:
        bal -= pts_req[r]; red_ix.append(ixs[k]); red_m.append(m); red_r.append(r); red_d.append(dts[k]); red_s.append(sts[k])
    bal += pts[k]
red = pd.DataFrame({'RedemptionID': np.arange(1,len(red_ix)+1), 'Date': pd.to_datetime(red_d), 'MemberID': red_m,
                    'StoreID': red_s, 'RewardID': rewards.RewardID.values[red_r], 'PointsSpent': pts_req[red_r],
                    'RewardCost': cost[red_r]})
tx.loc[red_ix, 'RedemptionID'] = red.RedemptionID.values
tx.loc[red_ix, 'Discount'] = np.minimum(disc_val[red_r], tx.loc[red_ix,'GrossSales'].values)
red['DiscountValue'] = tx.loc[red_ix, 'Discount'].values
tx['NetSales'] = np.round(tx.GrossSales - tx.Discount, 2)
print('redemptions', len(red))

# ---------------- campaigns (challenges) ----------------
camps = pd.DataFrame([
 (1,'New Year, New Ritual','Visit 8 times in January','Frequency','2025-01-02','2025-01-31',800),
 (2,'Spring Blend Explorer','Try 3 seasonal drinks','Product trial','2025-03-20','2025-04-20',600),
 (3,'Morning Streak','5 visits before 10am in 2 weeks','Daypart','2025-05-05','2025-05-18',500),
 (4,'Summer Cold Brew Club','Buy 6 cold brews','Product trial','2025-06-16','2025-08-31',900),
 (5,'Bring a Friend','Refer a friend who joins','Acquisition','2025-10-01','2025-10-31',1000),
 (6,'Pastry Pairing','Add food to 5 orders','Basket','2025-11-10','2025-12-07',600),
 (7,'Order Ahead Week','3 mobile orders in a week','Digital','2026-02-02','2026-02-15',450),
 (8,'Spring Blend Explorer II','Try 3 seasonal drinks','Product trial','2026-03-20','2026-04-20',600),
 (9,'Morning Streak II','5 visits before 10am in 2 weeks','Daypart','2026-05-11','2026-05-24',500),
 (10,'Summer Cold Brew Club II','Buy 6 cold brews','Product trial','2026-06-15','2026-08-31',900),
 (11,'Bring a Friend II','Refer a friend who joins','Acquisition','2026-09-01','2026-09-30',1000),
 (12,'Autumn Loyalty Sprint','Spend €60 in October','Spend','2026-10-01','2026-10-31',1200)],
 columns=['CampaignID','CampaignName','Mechanic','CampaignType','StartDate','EndDate','RewardPoints'])
camps['StartDate']=pd.to_datetime(camps.StartDate); camps['EndDate']=pd.to_datetime(camps.EndDate)
enr = []
mvis = tx[is_mem].groupby(['MemberID', tx[is_mem].Date.dt.to_period('M')]).size()
for _,c in camps.iterrows():
    pm = c.StartDate.to_period('M')
    active = mvis.xs(pm, level=1)
    cand = active.index.values; v = active.values
    p_en = np.clip(0.08 + 0.025*v, 0, 0.6) * (1.35 if c.CampaignType in ('Daypart','Frequency') else 1)
    take = rng.random(len(cand)) < p_en
    em = cand[take]; ev = v[take]
    ed = c.StartDate + pd.to_timedelta(rng.integers(0, max(1,(c.EndDate-c.StartDate).days//2), len(em)),'D')
    base_c = {'Frequency':.30,'Product trial':.42,'Daypart':.27,'Acquisition':.14,'Basket':.38,'Digital':.47,'Spend':.33}[c.CampaignType]
    pc = np.clip(base_c + 0.03*(ev-4), .05, .9)
    done = rng.random(len(em)) < pc
    cd = [ (d + pd.Timedelta(days=int(rng.integers(3, max(4,(c.EndDate-d).days+1))))) if dn else pd.NaT for d,dn in zip(ed,done)]
    cd = pd.Series(pd.to_datetime(cd)); cd = cd.where(cd.isna() | (cd <= c.EndDate), c.EndDate).values
    enr.append(pd.DataFrame({'CampaignID':c.CampaignID,'MemberID':em,'EnrolledDate':ed,'CompletedDate':cd}))
enr = pd.concat(enr, ignore_index=True); enr['MemberID'] = enr['MemberID'].astype(int)
enr.loc[enr.CompletedDate.notna() & (enr.CompletedDate > END),'CompletedDate'] = pd.NaT
enr.insert(0,'EnrollmentID', np.arange(1,len(enr)+1))
enr['PointsAwarded'] = np.where(enr.CompletedDate.notna(), enr.CampaignID.map(camps.set_index('CampaignID').RewardPoints), 0)
print('enrollments', len(enr), 'completion', enr.CompletedDate.notna().mean().round(3))

# ---------------- write ----------------
tx.insert(0,'TransactionID', np.arange(1,len(tx)+1))
tx['MemberID'] = tx['MemberID'].astype('Int64')
tx['RedemptionID'] = tx['RedemptionID'].replace(0, pd.NA).astype('Int64')
out_tx = tx[['TransactionID','Date','Hour','StoreID','MemberID','Channel','Items','HasFood','GrossSales','Discount','NetSales','PointsEarned','RedemptionID']]
out_tx.to_csv(f'{OUT}/fact_transactions.csv', index=False, date_format='%Y-%m-%d')
st[['StoreID','StoreName','City','Region','Format','OpenDate','SeatingCapacity']].to_csv(f'{OUT}/dim_store.csv', index=False, date_format='%Y-%m-%d')
mem[['MemberID','JoinDate','JoinChannel','AgeBand','Tier','HomeStoreID']].to_csv(f'{OUT}/dim_member.csv', index=False, date_format='%Y-%m-%d')
rewards[['RewardID','RewardName','RewardCategory','PointsRequired','UnitCost']].to_csv(f'{OUT}/dim_reward.csv', index=False)
red.to_csv(f'{OUT}/fact_redemptions.csv', index=False, date_format='%Y-%m-%d')
camps.to_csv(f'{OUT}/dim_campaign.csv', index=False, date_format='%Y-%m-%d')
enr.to_csv(f'{OUT}/fact_campaign_enrollments.csv', index=False, date_format='%Y-%m-%d')
print('transactions', len(out_tx))
