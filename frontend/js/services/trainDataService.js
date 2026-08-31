/**
 * RailOpt - Train Data Service & Provider Abstraction
 * Supports liveProvider, mockProvider, automatic fallback, and caching.
 */

import { mockTrainMovements } from "../mockData.js";

class MockTrainProvider {
    constructor() {
        this.name = "Synthetic Demo Data";
    }

    async getMovements() {
        return mockTrainMovements.map(t => ({
            train_id: t.trainNumber,
            train_name: t.trainName,
            train_type: t.trainType,
            section: t.origin === "NDLS" ? "NDLS-TKD" : (t.origin === "NZM" ? "TKD-FDB" : "FDB-PWL"),
            track_line: t.direction === "DN" ? "DN_MAIN" : "UP_MAIN",
            current_location: `En Route from ${t.origin}`,
            next_location: t.destination,
            scheduled_departure_min: t.departureMinute,
            scheduled_arrival_min: t.arrivalMinute,
            estimated_departure_min: t.departureMinute + (t.regulatedDelayMin || 0),
            estimated_arrival_min: t.arrivalMinute + (t.regulatedDelayMin || 0),
            scheduled_departure_str: t.departureTimeStr,
            scheduled_arrival_str: t.arrivalTimeStr,
            estimated_departure_str: t.departureTimeStr,
            estimated_arrival_str: t.arrivalTimeStr,
            delay_minutes: t.regulatedDelayMin || 0,
            status: (t.regulatedDelayMin || 0) === 0 ? "ON_TIME" : "DELAYED",
            direction: t.direction,
            priority_weight: t.priorityWeight,
            source: "Synthetic Demo Data",
            last_updated: new Date().toLocaleTimeString()
        }));
    }

    async getTrainStatus(trainId) {
        const list = await this.getMovements();
        return list.find(t => t.train_id === trainId) || null;
    }

    async getStationBoard(stationId) {
        const list = await this.getMovements();
        return list.filter(t => t.current_location.includes(stationId) || t.next_location.includes(stationId));
    }
}

class LiveTrainProvider {
    constructor() {
        this.name = "Live/Public Train Data";
        this.apiBase = "/api/trains";
    }

    async getMovements() {
        const res = await fetch(`${this.apiBase}/live`, { signal: AbortSignal.timeout(4000) });
        if (!res.ok) throw new Error(`Live provider returned ${res.status}`);
        const json = await res.json();
        return json.movements || [];
    }

    async getTrainStatus(trainId) {
        const res = await fetch(`${this.apiBase}/status/${trainId}`, { signal: AbortSignal.timeout(4000) });
        if (!res.ok) throw new Error(`Status error ${res.status}`);
        const json = await res.json();
        return json.movement || null;
    }

    async getStationBoard(stationId) {
        const list = await this.getMovements();
        return list.filter(t => t.current_location.includes(stationId) || t.next_location.includes(stationId));
    }
}

export class TrainDataService {
    constructor() {
        this.liveProvider = new LiveTrainProvider();
        this.mockProvider = new MockTrainProvider();
        this.cacheTTL = 30000; // 30 seconds
        this.lastFetchTime = 0;
        this.cachedData = null;
        this.currentSourceLabel = "Synthetic Demo Data";
        this.isFallback = true;
    }

    async getLiveTrainMovements(forceRefresh = false) {
        const now = Date.now();
        if (!forceRefresh && this.cachedData && (now - this.lastFetchTime < this.cacheTTL)) {
            return {
                source: this.currentSourceLabel,
                isFallback: this.isFallback,
                lastUpdated: new Date(this.lastFetchTime).toLocaleTimeString(),
                movements: this.cachedData
            };
        }

        let data = null;
        try {
            data = await this.liveProvider.getMovements();
            this.currentSourceLabel = "Live/Public Train Data";
            this.isFallback = false;
        } catch (err) {
            console.warn("Live train provider unavailable, falling back to mockProvider.", err.message);
            data = await this.mockProvider.getMovements();
            this.currentSourceLabel = "Synthetic Demo Data (Fallback)";
            this.isFallback = true;
        }

        this.cachedData = data;
        this.lastFetchTime = now;

        return {
            source: this.currentSourceLabel,
            isFallback: this.isFallback,
            lastUpdated: new Date(this.lastFetchTime).toLocaleTimeString(),
            movements: data
        };
    }

    async getTrainStatus(trainId) {
        try {
            return await this.liveProvider.getTrainStatus(trainId);
        } catch {
            return await this.mockProvider.getTrainStatus(trainId);
        }
    }

    async getStationBoard(stationId) {
        try {
            return await this.liveProvider.getStationBoard(stationId);
        } catch {
            return await this.mockProvider.getStationBoard(stationId);
        }
    }

    async simulateDelay(trainId, delayMinutes) {
        try {
            const res = await fetch("/api/trains/simulate-delay", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ train_id: trainId, delay_minutes: delayMinutes })
            });
            if (res.ok) {
                this.cachedData = null; // bust cache
                return await this.getLiveTrainMovements(true);
            }
        } catch (err) {
            console.warn("Backend simulate delay failed:", err);
        }
        return await this.getLiveTrainMovements(true);
    }
}

export const trainDataService = new TrainDataService();
