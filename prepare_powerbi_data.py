"""
Krannert Center — Power BI 数据准备脚本
=========================================
把 REDCap 原始 CSV 转换成 Power BI 可直接导入的结构化表格。
运行这个脚本后，把 output/ 文件夹里的所有 CSV 导入 Power BI 即可。
"""

import pandas as pd
import numpy as np
import os

# ── 配置 ─────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'CampusEngagementWith_DATA_2026-06-27_1054.csv')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 加载原始数据 ─────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, encoding='utf-8-sig')
df = df[df['record_id'] != 1].copy()  # 删除测试行
print(f'加载 {len(df)} 条有效记录')

# ══════════════════════════════════════════════════════════════════════
# 表格1: FACT_RESPONSES（核心事实表 — 每行一个受访者，所有数字评分汇聚于此）
# ══════════════════════════════════════════════════════════════════════
print('创建 FACT_RESPONSES...')

fact = df[['record_id']].copy()

# 人口统计列（直接映射）
fact['zip_code'] = df['zip_v2']
fact['academic_standing'] = df['undergrad_standing_v2'].map({1:'Freshman',2:'Sophomore',3:'Junior',4:'Senior'})
fact['attended_event'] = df['break_1_attendedvsnoattended'].map({1:'Yes',0:'No'})

# 观众分类（互斥分段，优先级: Student > Faculty/Staff > Community > Other）
is_student = df[['affiliation_v2___1','affiliation_v2___2']].sum(axis=1) > 0
is_facstaff = df[['affiliation_v2___3','affiliation_v2___4']].sum(axis=1) > 0
is_community = df['affiliation_v2___6'].astype(int) > 0

fact['audience_segment'] = 'Other'
fact.loc[is_student, 'audience_segment'] = 'Student'
fact.loc[is_facstaff & ~is_student, 'audience_segment'] = 'Faculty/Staff'
fact.loc[is_community & ~is_student & ~is_facstaff, 'audience_segment'] = 'Community'

# 弱势群体标识
fact['is_underrepresented'] = df[[f'underrepresented_group_v2___{i}' for i in range(2,8)]].sum(axis=1) > 0
fact['is_underrepresented_label'] = fact['is_underrepresented'].map({True:'Underrepresented', False:'Not Underrepresented'})

# 核心评分（1-5 Likert）
score_map = {
    'belonging_score': 'question401_v2',
    'representation_score': 'question403_v2',
    'cultural_affirming_score': 'question407_v2',
    'engagement_score': 'question501_v2',
    'accessibility_rating': 'question701_v2',
    'sensory_needs_met': 'question704_v2',
    'staff_welcoming': 'question801_v2',
    'patron_services_satisfaction': 'qestion802_v2',
    'ticket_experience': 'question803_v2',
    'mobile_ticket_ease': 'question804_v2',
    'informed_patron_services': 'qestion805_v2',
    'will_call_ready': 'question806_v2',
    'communication_effectiveness': 'question602_v2',
    # NPS (1-10), 工作坊评分
    'nps_score': 's12_q1_v2',
    'workshop_value': 'question1002_v2',
}

for new_col, orig_col in score_map.items():
    fact[new_col] = pd.to_numeric(df[orig_col], errors='coerce')

# 二进制列
fact['sensory_interest'] = df['question703_v2'].map({1:'Yes', 2:'No'})
fact['know_accessibility_nav'] = df['question705_v2'].map({1:'Yes', 2:'No'})
fact['attended_workshop'] = df['question1001_v2'].map({1:'Yes', 0:'No'})
fact['willing_further_research'] = df['s13_q1_v2'].map({'Yes':'Yes','Maybe':'Maybe','No':'No'})

# NPS 分类
fact['nps_category'] = pd.cut(
    fact['nps_score'],
    bins=[0, 6, 8, 10],
    labels=['Detractor (0-6)', 'Passive (7-8)', 'Promoter (9-10)'],
    right=True
)

# 归属感等级（用于热力图）
fact['belonging_level'] = fact['belonging_score'].map({
    1:'1-Not at All', 2:'2-Slightly', 3:'3-Moderately', 4:'4-Mostly', 5:'5-Completely'
})

fact.to_csv(os.path.join(OUTPUT_DIR, 'FACT_RESPONSES.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(fact)} 行, {len(fact.columns)} 列')

# ══════════════════════════════════════════════════════════════════════
# 表格2: DIM_AFFILIATION（身份类别 — 从checkbox Unpivot）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_AFFILIATION...')

AFFILIATION_LABELS = {
    'affiliation_v2___1': 'Undergraduate Student',
    'affiliation_v2___2': 'Graduate Student',
    'affiliation_v2___3': 'Faculty',
    'affiliation_v2___4': 'Staff',
    'affiliation_v2___5': 'KCPA Staff',
    'affiliation_v2___6': 'Community Member',
    'affiliation_v2___7': 'Engagement Partner',
    'affiliation_v2___8': 'Donor',
    'affiliation_v2___9': 'Visitor',
    'affiliation_v2___10': 'Other',
}

affil_rows = []
for _, row in df.iterrows():
    for col, label in AFFILIATION_LABELS.items():
        if row.get(col, 0) == 1:
            affil_rows.append({
                'record_id': row['record_id'],
                'affiliation_type': label,
                'audience_segment': fact.loc[fact['record_id']==row['record_id'], 'audience_segment'].values[0]
            })

dim_affil = pd.DataFrame(affil_rows)
dim_affil.to_csv(os.path.join(OUTPUT_DIR, 'DIM_AFFILIATION.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_affil)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格3: DIM_UNDERREP（弱势群体 — Unpivot）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_UNDERREP...')

UNDERREP_LABELS = {
    'underrepresented_group_v2___1': 'None (not underrepresented)',
    'underrepresented_group_v2___2': 'Racial/ethnic minority',
    'underrepresented_group_v2___3': 'Disability',
    'underrepresented_group_v2___4': 'LGBTQIA+',
    'underrepresented_group_v2___5': 'Veteran',
    'underrepresented_group_v2___6': 'First-generation college student',
    'underrepresented_group_v2___7': 'Rural background',
    'underrepresented_group_v2___8': 'Other',
}

underrep_rows = []
for _, row in df.iterrows():
    for col, label in UNDERREP_LABELS.items():
        if row.get(col, 0) == 1:
            underrep_rows.append({
                'record_id': row['record_id'],
                'underrep_group': label
            })

dim_underrep = pd.DataFrame(underrep_rows)
dim_underrep.to_csv(os.path.join(OUTPUT_DIR, 'DIM_UNDERREP.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_underrep)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格4: DIM_EVENT_TYPES（出席的活动类型 — Unpivot，仅出席者）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_EVENT_TYPES...')

EVENT_LABELS = {
    'question2_v2___1': 'Dance',
    'question2_v2___2': 'Classical Music',
    'question2_v2___3': 'Jazz',
    'question2_v2___4': 'World Music',
    'question2_v2___5': 'Theater',
    'question2_v2___6': 'Opera',
    'question2_v2___7': 'Film',
    'question2_v2___8': 'Lecture/Talk',
    'question2_v2___9': 'Workshop',
    'question2_v2___10': 'Family/Youth',
}

event_rows = []
df_att = df[df['break_1_attendedvsnoattended'] == 1]
for _, row in df_att.iterrows():
    for col, label in EVENT_LABELS.items():
        if row.get(col, 0) == 1:
            event_rows.append({
                'record_id': row['record_id'],
                'event_type': label,
                'audience_segment': fact.loc[fact['record_id']==row['record_id'], 'audience_segment'].values[0]
            })

dim_events = pd.DataFrame(event_rows)
dim_events.to_csv(os.path.join(OUTPUT_DIR, 'DIM_EVENT_TYPES.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_events)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格5: DIM_ATTEND_REASONS（出席原因 — Unpivot，仅出席者）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_ATTEND_REASONS...')

REASON_LABELS = {
    'question3_v2___1': 'Quality of performances',
    'question3_v2___2': 'Variety of programming',
    'question3_v2___3': 'Affordable price',
    'question3_v2___4': 'Convenient location',
    'question3_v2___5': 'Atmosphere/ambiance',
    'question3_v2___6': 'Social connection',
    'question3_v2___7': 'Learning/education',
    'question3_v2___8': 'Community engagement',
    'question3_v2___9': 'Other',
}

reason_rows = []
for _, row in df_att.iterrows():
    for col, label in REASON_LABELS.items():
        if row.get(col, 0) == 1:
            reason_rows.append({
                'record_id': row['record_id'],
                'attend_reason': label,
                'audience_segment': fact.loc[fact['record_id']==row['record_id'], 'audience_segment'].values[0]
            })

dim_reasons = pd.DataFrame(reason_rows)
dim_reasons.to_csv(os.path.join(OUTPUT_DIR, 'DIM_ATTEND_REASONS.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_reasons)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格6: DIM_BARRIERS（不参加的障碍 — Unpivot，仅未出席者）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_BARRIERS...')

BARRIER_LABELS = {
    'no_attend_question2_v3___1': 'Not interested',
    'no_attend_question2_v3___2': 'Ticket price too high',
    'no_attend_question2_v3___3': 'Schedule conflict',
    'no_attend_question2_v3___4': "Didn't know about events",
    'no_attend_question2_v3___5': 'No one to go with',
    'no_attend_question2_v3___6': 'Transportation',
    'no_attend_question2_v3___7': 'Parking',
    'no_attend_question2_v3___8': 'Accessibility issues',
    'no_attend_question2_v3___9': 'COVID-19 concerns',
    'no_attend_question2_v3___10': 'Other',
}

barrier_rows = []
df_non = df[df['break_1_attendedvsnoattended'] == 0]
for _, row in df_non.iterrows():
    for col, label in BARRIER_LABELS.items():
        if row.get(col, 0) == 1:
            barrier_rows.append({
                'record_id': row['record_id'],
                'barrier': label
            })

dim_barriers = pd.DataFrame(barrier_rows)
dim_barriers.to_csv(os.path.join(OUTPUT_DIR, 'DIM_BARRIERS.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_barriers)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格7: DIM_COMMUNICATION（传播渠道 — Unpivot）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_COMMUNICATION...')

COMM_LABELS = {
    'question601_v2___1': 'Website',
    'question601_v2___2': 'Email newsletters',
    'question601_v2___3': 'Social media',
    'question601_v2___4': 'Word of mouth',
    'question601_v2___5': 'Campus flyers/posters',
    'question601_v2___6': 'Other',
}

comm_rows = []
for _, row in df.iterrows():
    for col, label in COMM_LABELS.items():
        if row.get(col, 0) == 1:
            comm_rows.append({
                'record_id': row['record_id'],
                'communication_channel': label
            })

dim_comm = pd.DataFrame(comm_rows)
dim_comm.to_csv(os.path.join(OUTPUT_DIR, 'DIM_COMMUNICATION.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_comm)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格8: DIM_PATRON_TYPE（观众关系类型 — Unpivot）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_PATRON_TYPE...')

PATRON_LABELS = {
    'patron_v2___1': 'Attended ticketed performances',
    'patron_v2___2': 'Attended free student events',
    'patron_v2___3': 'Outreach/community events',
    'patron_v2___4': 'Pre/post-performance workshops',
    'patron_v2___5': 'Donated/sponsored',
    'patron_v2___6': 'Visited as guest',
    'patron_v2___7': 'First-time visitor',
    'patron_v2___8': 'Other',
}

patron_rows = []
for _, row in df_att.iterrows():
    for col, label in PATRON_LABELS.items():
        if row.get(col, 0) == 1:
            patron_rows.append({
                'record_id': row['record_id'],
                'patron_type': label
            })

dim_patron = pd.DataFrame(patron_rows)
dim_patron.to_csv(os.path.join(OUTPUT_DIR, 'DIM_PATRON_TYPE.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_patron)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格9: DIM_COLLEGE（学院 — Unpivot）
# ══════════════════════════════════════════════════════════════════════
print('创建 DIM_COLLEGE...')

COLLEGE_LABELS = {
    'colleges_2___1': 'Fine & Applied Arts',
    'colleges_2___2': 'Carle Medicine',
    'colleges_2___3': 'ACES',
    'colleges_2___4': 'Applied Health Sciences',
    'colleges_2___5': 'Education',
    'colleges_2___6': 'Law',
    'colleges_2___7': 'Liberal Arts & Sciences',
    'colleges_2___8': 'Media',
    'colleges_2___9': 'Veterinary Medicine',
    'colleges_2___10': 'General Studies',
    'colleges_2___11': 'Gies Business',
    'colleges_2___12': 'Graduate College',
    'colleges_2___13': 'Grainger Engineering',
    'colleges_2___14': 'Social Work',
    'colleges_2___15': 'iSchool',
    'colleges_2___16': 'Labor & Employment',
}

college_rows = []
for _, row in df.iterrows():
    for col, label in COLLEGE_LABELS.items():
        if row.get(col, 0) == 1:
            college_rows.append({
                'record_id': row['record_id'],
                'college': label
            })

dim_college = pd.DataFrame(college_rows)
dim_college.to_csv(os.path.join(OUTPUT_DIR, 'DIM_COLLEGE.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(dim_college)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格10: KPI_SUMMARY（预计算的KPI汇总 — 直接做卡片）
# ══════════════════════════════════════════════════════════════════════
print('创建 KPI_SUMMARY...')

kpi_data = []

# 出席者人数
attended = fact[fact['attended_event'] == 'Yes']
non_attended = fact[fact['attended_event'] == 'No']

# 归属感
bel_vals = attended['belonging_score'].dropna()
kpi_data.append({'KPI_Name': 'Overall Belonging Score (1-5)', 'Value': round(bel_vals.mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Belonging'})
kpi_data.append({'KPI_Name': 'Representation Score (1-5)', 'Value': round(attended['representation_score'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Belonging'})
kpi_data.append({'KPI_Name': 'Cultural Affirmation Score (1-5)', 'Value': round(attended['cultural_affirming_score'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Belonging'})

# NPS
nps_vals = fact['nps_score'].dropna()
promoters = (nps_vals >= 9).sum()
detractors = (nps_vals <= 6).sum()
nps_value = round(100 * (promoters - detractors) / len(nps_vals), 1)
kpi_data.append({'KPI_Name': 'NPS (Net Promoter Score)', 'Value': nps_value,
                 'Target': 50, 'Format': 'NPS', 'Category': 'NPS'})
kpi_data.append({'KPI_Name': 'Overall NPS Mean (1-10)', 'Value': round(nps_vals.mean(), 1),
                 'Target': 10, 'Format': 'Gauge', 'Category': 'NPS'})

# 无障碍
know_nav = attended['know_accessibility_nav'].dropna()
know_pct = round(100 * (know_nav == 'Yes').sum() / len(know_nav), 1)
kpi_data.append({'KPI_Name': '% Know Accessibility Navigation', 'Value': know_pct,
                 'Target': 80, 'Format': 'Percentage', 'Category': 'Accessibility'})
kpi_data.append({'KPI_Name': 'Accessibility Rating (1-5)', 'Value': round(attended['accessibility_rating'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Accessibility'})

# 观众服务
kpi_data.append({'KPI_Name': 'Staff Welcoming Score (1-5)', 'Value': round(attended['staff_welcoming'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Service'})
kpi_data.append({'KPI_Name': 'Mobile Ticket Ease (1-5)', 'Value': round(attended['mobile_ticket_ease'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Service'})
kpi_data.append({'KPI_Name': 'Patron Services Satisfaction (1-5)', 'Value': round(attended['patron_services_satisfaction'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Service'})

# 参与度
kpi_data.append({'KPI_Name': 'Engagement Score (1-5)', 'Value': round(attended['engagement_score'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Engagement'})
kpi_data.append({'KPI_Name': 'Communication Effectiveness (1-5)', 'Value': round(fact['communication_effectiveness'].dropna().mean(), 2),
                 'Target': 5.0, 'Format': 'Gauge', 'Category': 'Engagement'})
kpi_data.append({'KPI_Name': 'Workshop Participation Rate', 'Value': round(100 * (attended['attended_workshop']=='Yes').sum() / len(attended), 1),
                 'Target': 50, 'Format': 'Percentage', 'Category': 'Engagement'})

kpi_df = pd.DataFrame(kpi_data)
kpi_df.to_csv(os.path.join(OUTPUT_DIR, 'KPI_SUMMARY.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(kpi_df)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格11: NPS_DETAIL（NPS详细分解 — 做NPS分类图）
# ══════════════════════════════════════════════════════════════════════
print('创建 NPS_DETAIL...')

nps_detail = []
for seg in fact['audience_segment'].unique():
    subset = fact[fact['audience_segment'] == seg]['nps_score'].dropna()
    if len(subset) == 0:
        continue
    pro = (subset >= 9).sum()
    pas = ((subset >= 7) & (subset <= 8)).sum()
    det = (subset <= 6).sum()
    nps_detail.append({
        'audience_segment': seg,
        'NPS_Category': 'Promoter (9-10)',
        'Count': int(pro),
        'Percentage': round(100*pro/len(subset), 1)
    })
    nps_detail.append({
        'audience_segment': seg,
        'NPS_Category': 'Passive (7-8)',
        'Count': int(pas),
        'Percentage': round(100*pas/len(subset), 1)
    })
    nps_detail.append({
        'audience_segment': seg,
        'NPS_Category': 'Detractor (0-6)',
        'Count': int(det),
        'Percentage': round(100*det/len(subset), 1)
    })

nps_dd = pd.DataFrame(nps_detail)
nps_dd.to_csv(os.path.join(OUTPUT_DIR, 'NPS_DETAIL.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(nps_dd)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格12: SERVICE_SCORES（服务评分对比）
# ══════════════════════════════════════════════════════════════════════
print('创建 SERVICE_SCORES...')

service_cols = [
    ('Staff Welcoming', 'staff_welcoming'),
    ('Patron Services Satisfaction', 'patron_services_satisfaction'),
    ('Ticket Purchase Experience', 'ticket_experience'),
    ('Mobile Ticket Ease', 'mobile_ticket_ease'),
    ('Will Call Ready', 'will_call_ready'),
    ('Informed About Services', 'informed_patron_services'),
]

service_rows = []
for label, col in service_cols:
    vals = attended[col].dropna()
    service_rows.append({
        'Service_Dimension': label,
        'Average_Score': round(vals.mean(), 2),
        'Response_Count': len(vals),
        'Category': 'Patron Services'
    })

service_df = pd.DataFrame(service_rows)
service_df.to_csv(os.path.join(OUTPUT_DIR, 'SERVICE_SCORES.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(service_df)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格13: BELONGING_BY_SEGMENT（归属感按分类对比）
# ══════════════════════════════════════════════════════════════════════
print('创建 BELONGING_BY_SEGMENT...')

bel_seg_rows = []
for seg in ['Student', 'Faculty/Staff', 'Community', 'Other']:
    subset = attended[attended['audience_segment']==seg]
    if len(subset) == 0:
        continue
    for col, label in [('belonging_score','Belonging'), ('representation_score','Representation'), ('cultural_affirming_score','Cultural Affirmation')]:
        vals = subset[col].dropna()
        if len(vals) > 0:
            bel_seg_rows.append({
                'audience_segment': seg,
                'metric': label,
                'average_score': round(vals.mean(), 2),
                'response_count': len(vals)
            })

bel_seg_df = pd.DataFrame(bel_seg_rows)
bel_seg_df.to_csv(os.path.join(OUTPUT_DIR, 'BELONGING_BY_SEGMENT.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(bel_seg_df)} 行')

# ══════════════════════════════════════════════════════════════════════
# 表格14: GEO_DATA（地理分布 — 按邮编汇总）
# ══════════════════════════════════════════════════════════════════════
print('创建 GEO_DATA...')

geo = df[['zip_v2']].copy()
geo = geo[geo['zip_v2'].notna() & (geo['zip_v2'] != '')]
geo['zip_code'] = geo['zip_v2'].astype(str).str[:5]  # 取前5位
geo_summary = geo.groupby('zip_code').size().reset_index(name='respondent_count')
geo_summary = geo_summary.sort_values('respondent_count', ascending=False)
geo_summary.to_csv(os.path.join(OUTPUT_DIR, 'GEO_DATA.csv'), index=False, encoding='utf-8-sig')
print(f'  → {len(geo_summary)} 个邮编')

# ══════════════════════════════════════════════════════════════════════
# 完成
# ══════════════════════════════════════════════════════════════════════
print('\nAll done! Output files in:')
for f in sorted(os.listdir(OUTPUT_DIR)):
    size_kb = os.path.getsize(os.path.join(OUTPUT_DIR, f)) / 1024
    print(f'   📄 {f} ({size_kb:.1f} KB)')
print(f'\n共 {len(os.listdir(OUTPUT_DIR))} 个CSV文件，可直接导入 Power BI。')
