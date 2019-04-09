/// <reference path="../node_modules/moment/moment.d.ts" />
import * as common from "./common"

declare var UIkit: any;
declare var Chart: any;

common.documentLoaded().then(() => {
	const apiBasePath = window.apiBasePath;
	const webshop_edit_permission = "webshop_edit";
	const service_permission = "service";

	const root = document.getElementById("single-page-content");

	const future1 = common.ajax("GET", apiBasePath + "/statistics/membership/by_date", null);
	const future2 = common.ajax("GET", apiBasePath + "/statistics/lasertime/by_month", null);

	Promise.all([future1, future2]).then(data => {
		const membershipjson = data[0];
		const laserjson = data[1];
		addChart(root, membershipjson.data);
		addLaserChart(root, laserjson.data);
		addRandomCharts(root);
	})
	.catch(json => {
		UIkit.modal.alert("<h2>Couldn't load statistics</h2>" + json.message + " " + json.error);
	});
});

const colors = [
	"#e41a1c",
	"#377eb8",
	"#4daf4a",
	"#984ea3",
	"#ff7f00",
	"#ffff33",
]

var timeFormat = 'YYYY-MM-DD HH:mm';

function splitSeries (items: Array<any>) {
	const dates = [];
	const values = [];
	for (let i = 0; i < items.length; i++) {
		dates.push(new Date(items[i][0]));
		values.push(items[i][1]);
	}
	return { dates: dates, values: values };
}

function toPoints (items: Array<any>) {
	const values = [];
	for (let i = 0; i < items.length; i++) {
		values.push({ x: new Date(items[i][0]), y: items[i][1] });
	}
	return values;
}

function addChart(root: HTMLElement, data: any) {
	// lab = splitSeries(data.labmembership);
	// member = splitSeries(data.membership);
	const dataMembership = toPoints(data.membership);
	const dataLabaccess = toPoints(data.labaccess);

	const config = {
		type: 'line',
		data: {
			datasets: [{
				label: 'Föreningsmedlemmar',
				backgroundColor: "#FF000077",
				borderColor: colors[0],
				fill: false,
				data: dataMembership
			},
			{
				label: 'Labmedlemmar',
				backgroundColor: "#0000FF77",
				borderColor: colors[1],
				fill: false,
				data: dataLabaccess
			}
			],
		},
		options: {
			responsive: true,
			elements: {
				line: {
					tension: 0,
				},
				point:{
					radius: 1,
					hoverRadius: 3,
				}
			},
			tooltips: {
				mode: 'x',
				intersect: false,
			},
			title: {
				display: true,
				text: 'Medlemsskap'
			},
			scales: {
				xAxes: [{
					type: 'time',
					time: {
						parser: timeFormat,
						// round: 'day'
						tooltipFormat: 'll'
					},
					scaleLabel: {
						display: true,
						labelString: 'Datum'
					},
					ticks: {
						max: new Date()  // Set max data to the current date
					}
				}],
				yAxes: [{
					ticks: {
						min: 0
					},
					scaleLabel: {
						display: true,
						labelString: 'Antal'
					}
				}]
			},
			pan: {
				enabled: true,
				mode: 'x',
			},
			zoom: {
				enabled: true,
				mode: 'x',
			},
		}
	};

	const canvas = <HTMLCanvasElement>document.createElement("canvas");
	root.appendChild(canvas);
	canvas.width = 500;
	canvas.height = 300;
	const ctx = canvas.getContext('2d');
	const chart = new Chart(ctx, config);
}

function addRandomCharts(root: HTMLElement) {
	{
		const canvas = <HTMLCanvasElement>document.createElement("canvas");
		root.appendChild(canvas);
		canvas.width = 500;
		canvas.height = 300;
		const ctx = canvas.getContext('2d');

		// And for a doughnut chart
		const myDoughnutChart = new Chart(ctx, {
			type: 'doughnut',
			data: {
				datasets: [{
					"data": [0.1, 0.9],
					"backgroundColor": [
						colors[1],
						colors[0],
					]
				}],
				labels: [
					"Tid som du är på makerspace",
					"Annan tid som borde spenderas på makerspace",
				]
			},
			options: {
				title: {
					display: true,
					text: 'Motiverande fake-data'
				},
				legend: {
					position: 'top',
				}
			}
		});
	}
}

function addLaserChart(root: HTMLElement, data: any) {
	// lab = splitSeries(data.labmembership);
	// member = splitSeries(data.membership);

	const config = {
		type: 'bar',
		data: {
			datasets: [{
				label: 'Laserminuter',
				backgroundColor: "#FF000077",
				borderColor: colors[0],
				fill: false,
				data: toPoints(data),
				steppedLine: true,
			},
			],
		},
		options: {
			title: {
				display: true,
				text: 'Användning av laserskäraren',
			},
			scales: {
				xAxes: [{
					type: 'time',
					time: {
						parser: 'YYYY-MM',
						// round: 'month'
						tooltipFormat: 'll',
						unit: 'month',
					},
					scaleLabel: {
						display: true,
						labelString: 'Datum'
					}
				}],
				yAxes: [{
					ticks: {
						min: 0
					},
					scaleLabel: {
						display: true,
						labelString: 'Antal'
					}
				}]
			},
		}
	};

	const canvas = <HTMLCanvasElement>document.createElement("canvas");
	root.appendChild(canvas);
	canvas.width = 500;
	canvas.height = 300;
	const ctx = canvas.getContext('2d');
	const chart = new Chart(ctx, config);
}
 