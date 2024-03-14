<template>
    <div class="card shadow ">
        <div class="card-body">
            <div class="d-flex">
                <div class="me-auto p-2 fw-semibold">Latest status: {{ getLatestStatus() }}</div>
                <div class="btn-group" role="group" aria-label="Button group with nested dropdown">
                    <button type="button" class="btn btn-primary" @click="refreshData">Refresh</button>
                    <!-- Mode -->
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-primary dropdown-toggle" :class="menuMode.class" data-bs-toggle="dropdown">
                            {{ menuMode.text }}
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" @click="updateMode(0)">{{ menuMode.options[0] }}</a></li>
                            <li><a class="dropdown-item" @click="updateMode(1)">{{ menuMode.options[1] }}</a></li>
                        </ul>
                    </div>
                    <!-- Setting -->
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-primary dropdown-toggle" :class="menuSetting.class" data-bs-toggle="dropdown">
                            {{ menuSetting.text }}
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" @click="updateSetting(0)">{{ menuSetting.options[0] }}</a></li>
                            <li><a class="dropdown-item" @click="updateSetting(1)">{{ menuSetting.options[1] }}</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <hr>
            <Line :data="chartData" :options="chartOptions" />
            <div class="d-flex" style="padding: 10px 0;">
                <div class="me-auto p-2"></div>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-primary dropdown-toggle" :class="chartSizes.class" data-bs-toggle="dropdown">
                        {{ chartSizes.label }}
                    </button>
                    <ul class="dropdown-menu">
                        <li v-for="opt in chartSizes.options">
                            <a class="dropdown-item" @click="updateChartSize(opt)">{{ opt }}</a>
                        </li>
                    </ul>
                </div>
            </div>

            <div style="display: none;">
                <div>your content...</div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { ref } from 'vue'
import { toast } from 'vue3-toastify';
import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    PointElement,
    LineElement,
    CategoryScale,
    LinearScale,
    type ChartData,
    type ChartOptions
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend);

const _chartData = ref<ChartData<'line'>>({
    labels: [],
    datasets: []
});
const _chartOptions = ref<ChartOptions<'line'>>({
    responsive: true, // Adjust chart based on screen size
    maintainAspectRatio: true, // Allow for resizing without distortion
    plugins: {
    },
    scales: {
        x: {
            display: true
        },
        y: {
            display: true,
        }
    }
});
const _isVisible = ref(false);

var bkData: any = null;
var srvConf: any = null;

export default {
    components: { Line },
    data() {
        return {
            chartData: _chartData as any,
            chartOptions: _chartOptions as any,
            dataPoint: {} as any,
            isVisible: _isVisible as any,
            chartSizes: {
                class: "disabled",
                label: "Choose chart size [15]",
                choose: 15,
                options: [ 10, 15, 20, 30, 40, 50]
            },
            menuMode: {
                class: "disabled",
                text: "Loading",
                options: [
                    "Use ML Model",
                    "Manual Config"
                ]
            } as any,
            menuSetting: {
                class: "disabled",
                text: "Loaing",
                options: [
                    "Turn Off",
                    "Turn On",
                ]
            } as any,
        }
    },
    methods: {
        formatTimestamp(timestamp: number) {
            // Convert timestamp to milliseconds
            const date = new Date(timestamp);

            // Get date components
            const year = date.getFullYear();
            const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Months are zero-based
            const day = date.getDate().toString().padStart(2, '0');
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            const seconds = date.getSeconds().toString().padStart(2, '0');
            // const milliseconds = date.getMilliseconds().toString().padStart(3, '0');

            // Assemble datetime string
            const datetimeString = `${hours}:${minutes}:${seconds}`;
            // const datetimeString = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;

            return datetimeString;
        },
        refreshData() {
            let url = `${location.toString()}api/data?size=${this.chartSizes.choose}`
            fetch(url, { method: "GET" }).then((response) => {
                response.json().then((data) => {
                    let labels: any[] = [];
                    let datasets: any[] = [
                        {
                            label: 'Humidity (%)',
                            data: [],
                            borderColor: 'green',
                        },
                        {
                            label: 'Temperature (°C)',
                            data: [],
                            borderColor: 'blue',
                        },
                        {
                            label: 'Soil Moisture (%)',
                            data: [],
                            borderColor: 'purple',
                        },
                    ];

                    for (let i = data.length - 1; i >= 0; --i) {
                        const e = data[i];
                        labels.push(this.formatTimestamp(e[0]));
                        datasets[0].data.push(e[1]);
                        datasets[1].data.push(e[2]);
                        datasets[2].data.push(e[3]);
                    }

                    this.chartData = {
                        labels: labels,
                        datasets: datasets
                    }
                    bkData = data
                });
            }).catch((err) => {
                console.error(err);
            });
        },
        getLatestStatus() {
            if (bkData === undefined || bkData === null || bkData.length === 0) {
                return "Unknow";
            }
            const lastRecord = bkData[0];
            if (lastRecord[4] === 1) {
                return "Is running";
            }
            return "Off";
        },
        updateMode(mode: any) {
            this.menuMode.text = this.menuMode.options[mode];
            if (srvConf['mode'] != mode) {
                srvConf['mode'] = mode;
                this.saveConfig();
            }
        },
        updateSetting(idx: any) {
            this.menuSetting.text = this.menuSetting.options[idx];
            if (srvConf['setting'] != idx) {
                srvConf['setting'] = idx;
                this.saveConfig();
            }
        },
        updateChartSize(size: any) {
            this.chartSizes.choose = size;
            this.chartSizes.label = `Choose chart size [${size}]`;
            this.refreshData();
        },
        loadConfig() {
            let url = `${location.toString()}api/config`;
            fetch(url, { method: "GET" }).then((response) => {
                response.json().then((data) => {
                    srvConf = data;
                    this.menuMode.text = this.menuMode.options[srvConf['mode']];
                    this.menuSetting.text = this.menuSetting.options[srvConf['setting']];
                });
            }).catch((err) => {
                console.error(err);
            });
        },
        async saveConfig() {
            let url = `${location.toString()}api/config`;
            try {
                const response = await fetch(url, {
                    method: "PUT",
                    body: JSON.stringify(srvConf)
                });
                toast("Update config successfully!");
            } catch (err) {
                console.error(err);
                this.loadConfig();
            }
        },
        enable() {
            this.menuMode.class = "";
            this.chartSizes.class = "";
            this.menuSetting.class = "";
        },
    },
    created() {
        this.refreshData();
        this.loadConfig();
        this.enable();
        this.chartOptions.plugins["tooltip"] = {
            usePointStyle: true,
            external(args: any) {
                if (args.tooltip.dataPoints && args.tooltip.dataPoints.length > 0) {
                    let idx = args.tooltip.dataPoints[0].dataIndex;
                    let status = bkData[idx][4]
                    let action = bkData[idx][5] === -1 ? status : bkData[idx][5]
                    args.tooltip.body[0].lines.push(`Is running: ${status}`)
                    args.tooltip.body[0].lines.push(`Action: ${action}`)
                }
            },
        };
    },
}
</script>