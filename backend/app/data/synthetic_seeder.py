from sqlalchemy.orm import Session
from ..models.models import (
    Department, Section, TrackLine, MaintenanceResource,
    MaintenanceJob, TrainSchedule, BlockWindow
)

def seed_synthetic_data(db: Session, force: bool = False):
    if not force and db.query(Department).count() > 0:
        return

    # 1. Clear existing data if force
    if force:
        db.query(MaintenanceJob).delete()
        db.query(TrainSchedule).delete()
        db.query(BlockWindow).delete()
        db.query(MaintenanceResource).delete()
        db.query(TrackLine).delete()
        db.query(Section).delete()
        db.query(Department).delete()
        db.commit()

    # 2. Departments
    departments = [
        Department(code="ENG", name="Civil Engineering (Permanent Way & Bridges)", color="#003366", icon="construction"),
        Department(code="S_T", name="Signaling & Telecommunication", color="#0284c7", icon="cell_tower"),
        Department(code="TRD", name="Traction Distribution (OHE / Power)", color="#d97706", icon="bolt"),
        Department(code="MECH", name="Mechanical / Carriage & Wagon", color="#4b5563", icon="train"),
    ]
    db.add_all(departments)
    db.commit()
    dept_map = {d.code: d.id for d in db.query(Department).all()}

    # 3. Sections along Delhi - Agra Corridor (Northern / North Central Railway)
    sections = [
        Section(code="NDLS-TKD", start_station="New Delhi (NDLS)", end_station="Tuglakabad (TKD)", length_km=15.5, num_tracks=2, division="Delhi", max_speed_kmh=130),
        Section(code="TKD-FDB", start_station="Tuglakabad (TKD)", end_station="Faridabad (FDB)", length_km=14.2, num_tracks=3, division="Delhi", max_speed_kmh=130),
        Section(code="FDB-PWL", start_station="Faridabad (FDB)", end_station="Palwal (PWL)", length_km=32.0, num_tracks=3, division="Delhi", max_speed_kmh=160),
        Section(code="PWL-KDS", start_station="Palwal (PWL)", end_station="Kosi Kalan (KDS)", length_km=42.0, num_tracks=2, division="Agra", max_speed_kmh=160),
        Section(code="KDS-MTJ", start_station="Kosi Kalan (KDS)", end_station="Mathura Jn (MTJ)", length_km=44.5, num_tracks=2, division="Agra", max_speed_kmh=160),
        Section(code="MTJ-AGC", start_station="Mathura Jn (MTJ)", end_station="Agra Cantt (AGC)", length_km=53.8, num_tracks=2, division="Agra", max_speed_kmh=160),
    ]
    db.add_all(sections)
    db.commit()
    sec_map = {s.code: s for s in db.query(Section).all()}

    # 4. Track Lines for each Section
    track_lines = []
    for s in sections:
        sec_obj = sec_map[s.code]
        track_lines.append(TrackLine(section_id=sec_obj.id, line_code=f"{s.code}_UP", line_type="UP"))
        track_lines.append(TrackLine(section_id=sec_obj.id, line_code=f"{s.code}_DN", line_type="DN"))
        if sec_obj.num_tracks >= 3:
            track_lines.append(TrackLine(section_id=sec_obj.id, line_code=f"{s.code}_3RD", line_type="BIDIRECTIONAL"))
    db.add_all(track_lines)
    db.commit()
    track_map = {tl.line_code: tl.id for tl in db.query(TrackLine).all()}

    # 5. Heavy Machinery & Resources
    resources = [
        MaintenanceResource(code="RES-CSM-01", name="CSM 09-32 Continuous Action Tamping Machine", resource_type="MACHINE", department_code="ENG", home_depot="Tuglakabad", transit_speed_kmh=40.0),
        MaintenanceResource(code="RES-DTS-01", name="Dynamic Track Stabilizer (DTS-102)", resource_type="MACHINE", department_code="ENG", home_depot="Palwal", transit_speed_kmh=45.0),
        MaintenanceResource(code="RES-TW-01", name="8-Wheeler Self-Propelled OHE Tower Wagon", resource_type="TOWER_WAGON", department_code="TRD", home_depot="Faridabad", transit_speed_kmh=50.0),
        MaintenanceResource(code="RES-TW-02", name="OHE Inspection Ladder Vehicle (TRD-02)", resource_type="TOWER_WAGON", department_code="TRD", home_depot="Mathura", transit_speed_kmh=50.0),
        MaintenanceResource(code="RES-ST-01", name="Electronic Interlocking Diagnostic Mobile Unit", resource_type="CREW_VAN", department_code="S_T", home_depot="Mathura", transit_speed_kmh=60.0),
        MaintenanceResource(code="RES-PQRS-01", name="Plasser Quick Relaying System (Track Renewal)", resource_type="MACHINE", department_code="ENG", home_depot="Tuglakabad", transit_speed_kmh=35.0),
        MaintenanceResource(code="RES-USFD-01", name="Digital Ultrasonic Rail Flaw Detection Cart", resource_type="CART", department_code="ENG", home_depot="Agra", transit_speed_kmh=15.0),
    ]
    db.add_all(resources)
    db.commit()
    res_map = {r.code: r.id for r in db.query(MaintenanceResource).all()}

    # 6. Standard Corridor Block Windows (5-8 realistic maintenance windows)
    windows = [
        BlockWindow(window_code="WIN-FDB-PWL-NIGHT", section_id=sec_map["FDB-PWL"].id, track_line_id=track_map.get("FDB-PWL_UP"), start_minute=90, end_minute=330, window_type="CORRIDOR"),
        BlockWindow(window_code="WIN-PWL-KDS-NIGHT", section_id=sec_map["PWL-KDS"].id, track_line_id=track_map.get("PWL-KDS_DN"), start_minute=100, end_minute=340, window_type="CORRIDOR"),
        BlockWindow(window_code="WIN-TKD-FDB-NIGHT", section_id=sec_map["TKD-FDB"].id, track_line_id=track_map.get("TKD-FDB_UP"), start_minute=80, end_minute=300, window_type="CORRIDOR"),
        BlockWindow(window_code="WIN-MTJ-AGC-NIGHT", section_id=sec_map["MTJ-AGC"].id, track_line_id=track_map.get("MTJ-AGC_UP"), start_minute=120, end_minute=330, window_type="CORRIDOR"),
        BlockWindow(window_code="WIN-NDLS-TKD-NIGHT", section_id=sec_map["NDLS-TKD"].id, track_line_id=track_map.get("NDLS-TKD_UP"), start_minute=60, end_minute=240, window_type="CORRIDOR"),
        BlockWindow(window_code="WIN-FDB-PWL-AFT", section_id=sec_map["FDB-PWL"].id, track_line_id=track_map.get("FDB-PWL_3RD"), start_minute=720, end_minute=870, window_type="CORRIDOR"),
    ]
    db.add_all(windows)
    db.commit()

    # 7. Train Schedule (10–20 realistic train movements)
    trains = [
        # Premium Superfast Trains
        TrainSchedule(train_number="22436", train_name="Vande Bharat Express", train_type="VANDE_BHARAT", priority_weight=35, direction="DN", origin_station="NDLS", destination_station="BSB", departure_minute=360, arrival_minute=460), # 06:00 - 07:40
        TrainSchedule(train_number="12050", train_name="Gatimaan Express", train_type="VANDE_BHARAT", priority_weight=35, direction="DN", origin_station="NZM", destination_station="AGC", departure_minute=490, arrival_minute=590), # 08:10 - 09:50
        TrainSchedule(train_number="12952", train_name="Mumbai Tejas Rajdhani", train_type="RAJDHANI", priority_weight=35, direction="DN", origin_station="NDLS", destination_station="MMCT", departure_minute=1015, arrival_minute=1115), # 16:55 - 18:35
        TrainSchedule(train_number="12951", train_name="Mumbai Rajdhani (Return)", train_type="RAJDHANI", priority_weight=35, direction="UP", origin_station="MMCT", destination_station="NDLS", departure_minute=480, arrival_minute=580), # 08:00 - 09:40
        TrainSchedule(train_number="12002", train_name="Bhopal Shatabdi Express", train_type="RAJDHANI", priority_weight=30, direction="DN", origin_station="NDLS", destination_station="RKMP", departure_minute=375, arrival_minute=475), # 06:15 - 07:55
        
        # Mail / Express Trains
        TrainSchedule(train_number="12626", train_name="Kerala Express", train_type="EXPRESS", priority_weight=20, direction="DN", origin_station="NDLS", destination_station="TVC", departure_minute=1210, arrival_minute=1330), # 20:10 - 22:10
        TrainSchedule(train_number="12625", train_name="Kerala Express (UP)", train_type="EXPRESS", priority_weight=20, direction="UP", origin_station="TVC", destination_station="NDLS", departure_minute=780, arrival_minute=900), # 13:00 - 15:00
        TrainSchedule(train_number="12138", train_name="Punjab Mail", train_type="EXPRESS", priority_weight=15, direction="DN", origin_station="FZR", destination_station="CSMT", departure_minute=315, arrival_minute=435), # 05:15 - 07:15
        TrainSchedule(train_number="12414", train_name="Pooja Superfast Express", train_type="EXPRESS", priority_weight=15, direction="UP", origin_station="JAT", destination_station="AII", departure_minute=230, arrival_minute=340), # 03:50 - 05:40
        TrainSchedule(train_number="11058", train_name="Amritsar Express", train_type="EXPRESS", priority_weight=12, direction="DN", origin_station="ASR", destination_station="CSMT", departure_minute=690, arrival_minute=830), # 11:30 - 13:50
        TrainSchedule(train_number="12780", train_name="Goa Express", train_type="EXPRESS", priority_weight=15, direction="DN", origin_station="NZM", destination_station="VSG", departure_minute=900, arrival_minute=1020), # 15:00 - 17:00
        TrainSchedule(train_number="14212", train_name="Intercity Express", train_type="PASSENGER", priority_weight=10, direction="DN", origin_station="NDLS", destination_station="AGC", departure_minute=1060, arrival_minute=1200), # 17:40 - 20:00
        TrainSchedule(train_number="14211", train_name="Intercity Express (UP)", train_type="PASSENGER", priority_weight=10, direction="UP", origin_station="AGC", destination_station="NDLS", departure_minute=360, arrival_minute=500), # 06:00 - 08:20
        TrainSchedule(train_number="04408", train_name="Palwal-Delhi EMU Special", train_type="PASSENGER", priority_weight=10, direction="UP", origin_station="PWL", destination_station="NDLS", departure_minute=450, arrival_minute=540), # 07:30 - 09:00
        
        # Freight & Goods Trains
        TrainSchedule(train_number="CONRAJ-01", train_name="Container Cargo Special", train_type="FREIGHT", priority_weight=5, direction="DN", origin_station="TKD", destination_station="JNPT", departure_minute=90, arrival_minute=210), # 01:30 - 03:30
        TrainSchedule(train_number="BTPN-04", train_name="IOCL Petroleum Tanker Rake", train_type="FREIGHT", priority_weight=5, direction="UP", origin_station="MTJ", destination_station="TKD", departure_minute=150, arrival_minute=270), # 02:30 - 04:30
        TrainSchedule(train_number="BOXN-12", train_name="Thermal Coal Freight Rake", train_type="FREIGHT", priority_weight=5, direction="DN", origin_station="TKD", destination_station="AGC", departure_minute=620, arrival_minute=780), # 10:20 - 13:00
    ]
    db.add_all(trains)
    db.commit()

    # 8. Realistic Multi-Department Maintenance Demands (15-20 jobs across ENG, TRD, S&T, MECH)
    jobs = [
        # --- Section FDB-PWL UP Line (Shadow Block Opportunity 1: ENG + TRD + S&T) ---
        MaintenanceJob(
            job_code="JOB-ENG-101",
            title="Mechanized Track Tamping & Alignment (CSM 09-32)",
            department_id=dept_map["ENG"],
            section_id=sec_map["FDB-PWL"].id,
            track_line_id=track_map.get("FDB-PWL_UP"),
            duration_minutes=210,
            priority=5,
            urgency="CRITICAL",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            speed_restriction_kmh=30,
            required_resource_id=res_map.get("RES-CSM-01"),
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=90,
            latest_end_minute=360,
            description="Deep tamping of KM 42/1 to 48/5 on UP Main line to eliminate severe gauge and cross-level variations detected by OMS car."
        ),
        MaintenanceJob(
            job_code="JOB-TRD-201",
            title="Annual OHE Cantilever & Contact Wire Overhaul",
            department_id=dept_map["TRD"],
            section_id=sec_map["FDB-PWL"].id,
            track_line_id=track_map.get("FDB-PWL_UP"),
            duration_minutes=180,
            priority=4,
            urgency="HIGH",
            requires_power_block=True,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            required_resource_id=res_map.get("RES-TW-01"),
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=90,
            latest_end_minute=360,
            description="Re-tensioning contact wire and replacement of defective composite insulators between Mast 44/12 and 46/20."
        ),
        MaintenanceJob(
            job_code="JOB-ST-302",
            title="High-Speed Multi-Section Digital Axle Counter (MSDAC) Calibration",
            department_id=dept_map["S_T"],
            section_id=sec_map["FDB-PWL"].id,
            track_line_id=track_map.get("FDB-PWL_UP"),
            duration_minutes=90,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=90,
            latest_end_minute=360,
            description="Quarterly calibration and tuning of track-mounted wheel detection sensor heads on UP high-speed line."
        ),

        # --- Section PWL-KDS DN Line (Shadow Block Opportunity 2: ENG + TRD) ---
        MaintenanceJob(
            job_code="JOB-ENG-102",
            title="Ballast Cleaning & Dynamic Track Stabilization",
            department_id=dept_map["ENG"],
            section_id=sec_map["PWL-KDS"].id,
            track_line_id=track_map.get("PWL-KDS_DN"),
            duration_minutes=240,
            priority=4,
            urgency="HIGH",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            speed_restriction_kmh=30,
            required_resource_id=res_map.get("RES-DTS-01"),
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=100,
            latest_end_minute=360,
            description="Deep ballast screening on KM 78/4 to 81/2 DN line followed by dynamic compaction to restore track elasticity."
        ),
        MaintenanceJob(
            job_code="JOB-TRD-202",
            title="Isolator Switch & Neutral Section Inspection",
            department_id=dept_map["TRD"],
            section_id=sec_map["PWL-KDS"].id,
            track_line_id=track_map.get("PWL-KDS_DN"),
            duration_minutes=150,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=True,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            required_resource_id=res_map.get("RES-TW-02"),
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=100,
            latest_end_minute=360,
            description="Preventive thermo-vision thermography defect rectification on Section Isolator SI-82/1."
        ),

        # --- Section TKD-FDB DN Line (Signaling & Interlocking) ---
        MaintenanceJob(
            job_code="JOB-ST-301",
            title="Electronic Interlocking Point Machine 104A/B Overhaul",
            department_id=dept_map["S_T"],
            section_id=sec_map["TKD-FDB"].id,
            track_line_id=track_map.get("TKD-FDB_DN"),
            duration_minutes=120,
            priority=4,
            urgency="HIGH",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            speed_restriction_kmh=45,
            required_resource_id=res_map.get("RES-ST-01"),
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=80,
            latest_end_minute=300,
            description="Replacement of drive motor and ground connections on crossover point 104A/B at Tuglakabad South cabin."
        ),

        # --- Section MTJ-AGC UP Line ---
        MaintenanceJob(
            job_code="JOB-ENG-103",
            title="Ultrasonic Flaw Detection (USFD) Rail Testing & Weld Examination",
            department_id=dept_map["ENG"],
            section_id=sec_map["MTJ-AGC"].id,
            track_line_id=track_map.get("MTJ-AGC_UP"),
            duration_minutes=150,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            required_resource_id=res_map.get("RES-USFD-01"),
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=120,
            latest_end_minute=360,
            description="Digital ultrasonic flaw detection on thermit welds and continuous welded rail segments."
        ),

        # --- Section NDLS-TKD UP Line ---
        MaintenanceJob(
            job_code="JOB-ST-303",
            title="Automatic Block Signal LED Retrofit & Tail Cable Check",
            department_id=dept_map["S_T"],
            section_id=sec_map["NDLS-TKD"].id,
            track_line_id=track_map.get("NDLS-TKD_UP"),
            duration_minutes=90,
            priority=2,
            urgency="ROUTINE",
            requires_power_block=False,
            requires_traffic_block=False,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=60,
            latest_end_minute=360,
            description="Routine replacement of red/yellow LED signal units on Auto Signals AS-12 and AS-14."
        ),

        # --- Section FDB-PWL 3rd Goods Line (Afternoon Window) ---
        MaintenanceJob(
            job_code="JOB-ENG-104",
            title="Turnout Sleepers Replacement on 3rd Goods Line",
            department_id=dept_map["ENG"],
            section_id=sec_map["FDB-PWL"].id,
            track_line_id=track_map.get("FDB-PWL_3RD"),
            duration_minutes=120,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=720,
            latest_end_minute=900,
            description="Replacement of damaged concrete sleepers on goods loop turnout #208."
        ),

        # --- Section TKD-FDB 3rd Line ---
        MaintenanceJob(
            job_code="JOB-MECH-401",
            title="Freight Yard Brake Rigging & Air Brake Testing Block",
            department_id=dept_map["MECH"],
            section_id=sec_map["TKD-FDB"].id,
            track_line_id=track_map.get("TKD-FDB_3RD"),
            duration_minutes=120,
            priority=2,
            urgency="ROUTINE",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=600,
            latest_end_minute=780,
            description="Intensive rolling stock safety audit on container rake line 4."
        ),

        # --- Additional Realistic Jobs 11 to 16 ---
        MaintenanceJob(
            job_code="JOB-ENG-105",
            title="Glued Insulated Rail Joint (GJ) Replacement",
            department_id=dept_map["ENG"],
            section_id=sec_map["TKD-FDB"].id,
            track_line_id=track_map.get("TKD-FDB_UP"),
            duration_minutes=120,
            priority=4,
            urgency="HIGH",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            speed_restriction_kmh=45,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=80,
            latest_end_minute=300,
            description="Re-insulation and replacement of aged glued joint at TKD up departure signal."
        ),
        MaintenanceJob(
            job_code="JOB-TRD-203",
            title="OHE Dropper & Jumper Replacement Gang Block",
            department_id=dept_map["TRD"],
            section_id=sec_map["TKD-FDB"].id,
            track_line_id=track_map.get("TKD-FDB_UP"),
            duration_minutes=100,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=True,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=80,
            latest_end_minute=300,
            description="Routine renewal of flexible copper droppers on mainline section."
        ),
        MaintenanceJob(
            job_code="JOB-ST-304",
            title="Track Circuit Audio Frequency (AFTC) Tuning & Testing",
            department_id=dept_map["S_T"],
            section_id=sec_map["KDS-MTJ"].id,
            track_line_id=track_map.get("KDS-MTJ_DN"),
            duration_minutes=90,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=100,
            latest_end_minute=360,
            description="End-to-end tuning of jointless audio frequency track circuits on automatic signaling territory."
        ),
        MaintenanceJob(
            job_code="JOB-ENG-106",
            title="Bridge Pier Scour Inspection & Girder Greasing",
            department_id=dept_map["ENG"],
            section_id=sec_map["MTJ-AGC"].id,
            track_line_id=track_map.get("MTJ-AGC_DN"),
            duration_minutes=150,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=False,
            requires_traffic_block=True,
            requires_speed_restriction=True,
            speed_restriction_kmh=50,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=120,
            latest_end_minute=360,
            description="Major steel girder bridge #114 bearing inspection and greasing over Yamuna canal."
        ),
        MaintenanceJob(
            job_code="JOB-TRD-204",
            title="Substation Feeder Circuit Breaker Maintenance",
            department_id=dept_map["TRD"],
            section_id=sec_map["NDLS-TKD"].id,
            track_line_id=track_map.get("NDLS-TKD_DN"),
            duration_minutes=120,
            priority=3,
            urgency="MEDIUM",
            requires_power_block=True,
            requires_traffic_block=False,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=60,
            latest_end_minute=240,
            description="25kV Traction Substation SF6 breaker preventive servicing."
        ),
        MaintenanceJob(
            job_code="JOB-ST-305",
            title="Level Crossing (LC Gate #34) Interlocking Audit",
            department_id=dept_map["S_T"],
            section_id=sec_map["PWL-KDS"].id,
            track_line_id=track_map.get("PWL-KDS_UP"),
            duration_minutes=75,
            priority=2,
            urgency="ROUTINE",
            requires_power_block=False,
            requires_traffic_block=False,
            requires_speed_restriction=False,
            status="PENDING",
            requested_date="2026-09-01",
            earliest_start_minute=100,
            latest_end_minute=360,
            description="Boom lock alignment and telephone circuitry check at interlocked gate #34."
        )
    ]
    db.add_all(jobs)
    db.commit()
    print("Database successfully seeded with 16 realistic multi-department jobs, 17 trains, and 6 block windows.")
