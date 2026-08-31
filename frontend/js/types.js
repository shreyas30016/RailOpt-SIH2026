/**
 * RailOpt - Indian Railways Block Planning & Optimization
 * Domain Type Definitions and Schemas
 * 
 * Defines core domain interfaces for:
 * 1. MaintenanceJob
 * 2. TrainMovement
 * 3. BlockWindow
 * 4. Constraint
 * 5. OptimizedPlan
 * 6. PlanChange
 */

/**
 * @typedef {Object} MaintenanceJob
 * @property {string} id - Unique identifier (e.g., "JOB-ENG-101")
 * @property {string} title - Human-readable job name
 * @property {'ENG' | 'S_T' | 'TRD' | 'MECH'} department - Department code
 * @property {string} departmentName - Full department name
 * @property {string} section - Corridor section (e.g., "FDB-PWL")
 * @property {string} trackLine - Line type ("UP_MAIN", "DN_MAIN", "3RD_LINE")
 * @property {number} durationMinutes - Duration in minutes (e.g., 180)
 * @property {1 | 2 | 3 | 4 | 5} priority - Priority weight (5 is emergency/critical)
 * @property {'CRITICAL' | 'HIGH' | 'MEDIUM' | 'ROUTINE'} urgency - Urgency tier
 * @property {boolean} requiresPowerBlock - True if TRD OHE power isolation is required
 * @property {boolean} requiresTrafficBlock - True if train traffic must be halted on line
 * @property {boolean} requiresSpeedRestriction - True if speed restriction follows work
 * @property {number} [speedRestrictionKmh] - Speed limit in km/h if applicable
 * @property {string} [requiredResource] - Heavy machinery code (e.g., "CSM 09-32 Tamping")
 * @property {'PENDING' | 'SCHEDULED' | 'APPROVED' | 'DEFERRED' | 'IN_PROGRESS'} status - Current status
 * @property {string} requestedDate - Date format "YYYY-MM-DD"
 * @property {number} earliestStartMinute - Minute offset from 00:00 (0-1440)
 * @property {number} latestEndMinute - Minute offset from 00:00 (0-1440)
 * @property {string} [description] - Detailed engineering notes
 */

/**
 * @typedef {Object} TrainMovement
 * @property {string} trainNumber - e.g., "22436", "12050", "CONRAJ-01"
 * @property {string} trainName - e.g., "Vande Bharat Express", "Container Freight"
 * @property {'VANDE_BHARAT' | 'RAJDHANI' | 'EXPRESS' | 'PASSENGER' | 'FREIGHT'} trainType - Train category
 * @property {number} priorityWeight - Priority score (Vande Bharat = 35, Express = 15-20, Freight = 5)
 * @property {'UP' | 'DN' | 'BIDIRECTIONAL'} direction - Direction of movement
 * @property {string} origin - Origin station code (e.g., "NDLS")
 * @property {string} destination - Destination station code (e.g., "AGC")
 * @property {number} departureMinute - Departure minute (0-1440)
 * @property {number} arrivalMinute - Arrival minute (0-1440)
 * @property {string} departureTimeStr - Format "HH:MM"
 * @property {string} arrivalTimeStr - Format "HH:MM"
 * @property {number} [regulatedDelayMin] - Accumulated regulation delay in minutes
 * @property {Array<{section: string, entryMinute: number, exitMinute: number}>} [routePassages] - Passage schedule
 */

/**
 * @typedef {Object} BlockWindow
 * @property {string} id - Window identifier (e.g., "WIN-FDB-PWL-NIGHT")
 * @property {string} section - Corridor section (e.g., "FDB-PWL")
 * @property {string} trackLine - Line code (e.g., "FDB-PWL_UP")
 * @property {number} startMinute - Start minute offset (e.g., 90 for 01:30)
 * @property {number} endMinute - End minute offset (e.g., 330 for 05:30)
 * @property {string} startTimeStr - Format "HH:MM"
 * @property {string} endTimeStr - Format "HH:MM"
 * @property {'CORRIDOR' | 'SHADOW' | 'EMERGENCY' | 'MAINTENANCE_LULL'} windowType - Window classification
 * @property {boolean} isActive - Active availability flag
 * @property {number} maxCapacityHours - Total allowable block time
 */

/**
 * @typedef {Object} Constraint
 * @property {string} id - Constraint code (e.g., "RULE-PWR-01", "RULE-TRACK-02")
 * @property {string} name - Rule name (e.g., "Traction Power Isolation Coupling")
 * @property {'HARD' | 'SOFT'} type - Hard physical vs soft operational optimization rule
 * @property {'SAFETY' | 'RESOURCE' | 'HEADWAY' | 'SHADOW_SYNERGY' | 'SPEED_RESTRICTION'} category - Category
 * @property {string} description - Mathematical/Operational definition
 * @property {boolean} isEnabled - Active toggle
 * @property {number} penaltyOrBonusWeight - Weight penalty/bonus in solver objective
 * @property {string} mathematicalFormulation - Constraint formulation expression
 */

/**
 * @typedef {Object} ScheduledBlock
 * @property {string} blockId - Unique block ID
 * @property {string} jobId - Associated MaintenanceJob ID
 * @property {string} title - Block title
 * @property {'ENG' | 'S_T' | 'TRD' | 'MECH'} department - Department code
 * @property {string} departmentColor - HEX color token
 * @property {string} section - Section code
 * @property {string} trackLine - Track Line code
 * @property {number} startMinute - Scheduled start minute
 * @property {number} endMinute - Scheduled end minute
 * @property {string} startTimeStr - Format "HH:MM"
 * @property {string} endTimeStr - Format "HH:MM"
 * @property {number} durationMinutes - Duration in minutes
 * @property {boolean} isShadowBlock - True if co-located with other department blocks
 * @property {string[]} pairedJobIds - IDs of shadow-paired jobs
 * @property {string} [resourceAssigned] - Allocated machine/gang
 * @property {Array<{trainNumber: string, delayMin: number, action: string}>} affectedTrains - Impacted train regulations
 * @property {string} decisionExplanation - Human-readable explanation of solver decision
 */

/**
 * @typedef {Object} UnscheduledJob
 * @property {string} jobId - Associated MaintenanceJob ID
 * @property {string} title - Job title
 * @property {'ENG' | 'S_T' | 'TRD' | 'MECH'} department - Department code
 * @property {string} section - Section code
 * @property {number} durationMinutes - Duration in minutes
 * @property {number} priority - Priority (1-5)
 * @property {string} unfeasibilityReason - Reason for exclusion / deferral
 * @property {string} suggestedAlternative - Recommendation for next maintenance cycle
 */

/**
 * @typedef {Object} ConflictLog
 * @property {string} id - Conflict identifier
 * @property {'TRACK_OCCUPANCY' | 'MACHINE_CONFLICT' | 'POWER_ISOLATION_MISMATCH' | 'TRAIN_HEADWAY'} conflictType - Type
 * @property {'RESOLVED' | 'PREVENTED' | 'UNRESOLVED'} severity - Status
 * @property {string} description - Description of conflict
 * @property {string} resolutionApplied - Automatic resolution applied by optimizer
 */

/**
 * @typedef {Object} OptimizedPlan
 * @property {number} runId - Optimization run identifier
 * @property {string} timestamp - Run timestamp "YYYY-MM-DD HH:MM:SS"
 * @property {'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE'} status - Solver status
 * @property {number} totalJobsConsidered - Count of total jobs evaluated
 * @property {number} scheduledJobsCount - Number of jobs scheduled
 * @property {number} unscheduledJobsCount - Number of jobs deferred
 * @property {number} totalMaintenanceHours - Total allocated maintenance hours
 * @property {number} totalTrainDelayMinutes - Total passenger + freight delay
 * @property {number} blockUtilizationPct - Corridor block window utilization percentage
 * @property {number} shadowBlockSynergyPct - Percentage of blocks executed as shadow blocks
 * @property {number} objectiveScore - Mathematical objective value
 * @property {number} solverTimeSeconds - Execution time in seconds
 * @property {ScheduledBlock[]} scheduledBlocks - List of scheduled block items
 * @property {UnscheduledJob[]} unscheduledJobs - List of unscheduled job items
 * @property {ConflictLog[]} conflictsResolved - Audit trail of resolved conflicts
 */

/**
 * @typedef {Object} PlanChange
 * @property {string} scenarioName - Scenario identifier
 * @property {number} baselineRunId - Baseline run ID
 * @property {OptimizedPlan} simulatedPlan - New simulated optimization plan
 * @property {number} deltaScheduledJobs - Change in scheduled jobs (+/-)
 * @property {number} deltaTrainDelayMinutes - Change in total train delay (+/-)
 * @property {number} deltaUtilizationPct - Change in corridor utilization (+/-)
 * @property {string[]} criticalAlerts - Safety and operational alerts
 * @property {string} impactSummary - High-level summary of simulation impact
 */

export {};
