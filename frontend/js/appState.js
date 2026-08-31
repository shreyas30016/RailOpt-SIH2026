/**
 * RailOpt - Centralized Application State Management
 * Provides a single predictable state store across all screens and components.
 */

class AppState {
    constructor() {
        this.state = {
            currentPage: "dashboard",
            selectedJobId: null,
            selectedBlockId: null,
            filters: {
                department: "ALL",
                urgency: "ALL",
                section: "ALL",
                status: "ALL",
                searchQuery: ""
            },
            optimizationResult: null,
            isOptimizing: false,
            whatIfScenario: {
                type: "TRAIN_DELAY",
                trainId: "12050",
                delayMinutes: 20,
                emergencyJob: null,
                simulationResult: null,
                isSimulating: false
            },
            modal: {
                isOpen: false,
                type: null, // "JOB_DETAIL", "DECISION_AUDIT", "NEW_REQUEST", "CONFIRM"
                data: null
            },
            liveDataMode: "AUTO" // "AUTO", "LIVE", "MOCK"
        };
        this.listeners = [];
    }

    getState() {
        return this.state;
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify() {
        for (const listener of this.listeners) {
            try {
                listener(this.state);
            } catch (err) {
                console.error("State listener error:", err);
            }
        }
    }

    setState(partialState) {
        this.state = { ...this.state, ...partialState };
        this.notify();
    }

    setFilters(filterUpdates) {
        this.state.filters = { ...this.state.filters, ...filterUpdates };
        this.notify();
    }

    setOptimizationResult(result) {
        this.state.optimizationResult = result;
        this.state.isOptimizing = false;
        this.notify();
    }

    setWhatIfSimulation(simResult) {
        this.state.whatIfScenario.simulationResult = simResult;
        this.state.whatIfScenario.isSimulating = false;
        this.notify();
    }

    openModal(type, data = null) {
        this.state.modal = {
            isOpen: true,
            type: type,
            data: data
        };
        this.notify();
    }

    closeModal() {
        this.state.modal = {
            isOpen: false,
            type: null,
            data: null
        };
        this.notify();
    }
}

export const appState = new AppState();
