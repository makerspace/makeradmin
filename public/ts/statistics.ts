/// <reference path="../node_modules/moment/moment.d.ts" />
import * as common from "./common";
//import * as moment from 'moment';
import * as d3 from "d3";
import {
    sankey,
    sankeyLeft,
    sankeyLinkHorizontal
} from "d3-sankey";
import "moment/locale/sv";
import { ServerResponse } from "./common";
import { Product, WellKnownProductId } from "./payment_common";
import { Quiz } from "./quiz";

declare var UIkit: any;
declare var Chart: any;

common.documentLoaded().then(() => {
    const apiBasePath = window.apiBasePath;

    const root = document.getElementById("single-page-content")!;

    const future1 = common.ajax(
        "GET",
        apiBasePath + "/statistics/membership/by_date",
        null,
    );
    const future2 = common.ajax(
        "GET",
        apiBasePath + "/statistics/lasertime/by_month",
        null,
    );
    const future3 = common.ajax(
        "GET",
        apiBasePath + "/quiz/quiz",
        null,
    ) as Promise<ServerResponse<Quiz[]>>;
    const future4 = common.ajax(
        "GET",
        apiBasePath + "/statistics/shop/statistics",
        null,
    ) as Promise<ServerResponse<ProductStatistics>>;
    const future5 = common.ajax(
        "GET",
        apiBasePath + "/statistics/membership/distribution_by_month",
        null,
    ) as Promise<ServerResponse<MemberDistribution>>;
    const future6 = common.ajax(
        "GET",
        apiBasePath + "/statistics/membership/distribution_by_month2",
        null,
    ) as Promise<ServerResponse<MemberDistribution>>;
    const future7 = common.ajax(
        "GET",
        apiBasePath + "/statistics/retention_graph",
        null,
    ) as Promise<ServerResponse<RetentionGraph>>;

    Promise.all([future1, future2, future3, future4, future5, future6, future7])
        .then((data) => {
            const membershipjson = data[0];
            const laserjson = data[1];
            addRetentionChart(root, data[6].data);
            addChart(root, membershipjson.data);
            addSubscriptionsChart(root, data[3].data);
            addLaserChart(root, laserjson.data);
            for (let quiz of data[2].data) {
                const quiz_future = common.ajax(
                    "GET",
                    apiBasePath + `/quiz/quiz/${quiz.id}/statistics`,
                ) as Promise<ServerResponse<QuizStatistics>>;
                quiz_future.then((data) => {
                    addQuizChart(root, data.data, quiz);
                });
            }
            addProductPurchasedChart(root, data[3].data);
            addMemberDistribution(
                root,
                data[4].data,
                "Of all members who became members at least one year ago, how many months have they had active lab membership during the last 12 months.",
            );
            addMemberDistribution(
                root,
                data[5].data,
                "Among all members, how many months have they had active lab membership during the last 12 months.",
            );
        })
        .catch((json) => {
            UIkit.modal.alert(
                "<h2>Couldn't load statistics</h2>" +
                json.message +
                " " +
                json.error,
            );
        });
});

const colors = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#ffff33",
];

var timeFormat = "YYYY-MM-DD HH:mm";

function toPoints(items: Array<any>) {
    const values = [];
    for (let i = 0; i < items.length; i++) {
        values.push({ x: new Date(items[i][0]), y: items[i][1] });
    }
    return values;
}

function filterDuplicates(items: Array<any>) {
    const newValues = [];
    for (let i = 0; i < items.length; i++) {
        if (i == 0 || items[i].x != items[i - 1].x) {
            newValues.push(items[i]);
        }
    }
    return newValues;
}

function maxOfSeries(items: Array<any>) {
    let mx = null;
    for (let i = 0; i < items.length; i++) {
        if (mx == null || items[i].y > mx.y) {
            mx = items[i];
        }
    }
    return mx;
}

function date2str(date: String | Date) {
    if (date instanceof Date) return date.toISOString().split("T")[0];
    else return date;
}

function pointAtDate(items: Array<any>, date: Date) {
    let best = null;
    for (let i = 0; i < items.length; i++) {
        if (best == null || items[i].x <= date) {
            best = items[i];
        }
    }
    return best;
}

function addSubscriptionsChart(root: HTMLElement, data: ProductStatistics) {
    const config = {
        type: "horizontalBar",
        data: {
            labels: [
                "Total members",
                "Has no subscription",
                "Has membership sub (maybe more)",
                "Has access sub (maybe more)",
                "Has both subs"
            ],
            datasets: [
                {
                    label: "Members",
                    backgroundColor: "#FF000077",
                    borderColor: colors[0],
                    data: [
                        data.subscription_split.active_members,
                        data.subscription_split.active_members - data.subscription_split.has_membership_sub - data.subscription_split.has_makerspace_access_sub + data.subscription_split.has_both_subs,
                        data.subscription_split.has_membership_sub,
                        data.subscription_split.has_makerspace_access_sub,
                        data.subscription_split.has_both_subs
                    ],
                }
            ],
        },
        options: {
            title: {
                display: true,
                text: "Antal medlemmar med olika typer av prenumerationer",
            },
            responsive: true,
            scales: {
                xAxes: [
                    {
                        stacked: false,
                    },
                ],
                yAxes: [
                    {
                        stacked: true,
                    },
                ],
            },
        },
    };

    const stats = document.createElement("div") as HTMLDivElement;

    stats.innerHTML = `
	<h3>Statistics for Subscriptions</h3>
	<canvas width=500 height=300></canvas>
	`;
    stats.className = "statistics-member-stats";

    const canvas = stats.querySelector("canvas")!;
    root.appendChild(stats);
    canvas.width = 500;
    canvas.height = 300;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, config);
}

function addChart(root: HTMLElement, data: any) {
    const dataMembership = filterDuplicates(toPoints(data.membership));
    const dataLabaccess = filterDuplicates(toPoints(data.labaccess));
    const maxtime = new Date();

    const config = {
        type: "line",
        data: {
            datasets: [
                {
                    label: "Föreningsmedlemmar",
                    backgroundColor: "#FF000077",
                    borderColor: colors[0],
                    fill: false,
                    data: dataMembership,
                },
                {
                    label: "Labmedlemmar",
                    backgroundColor: "#0000FF77",
                    borderColor: colors[1],
                    fill: false,
                    data: dataLabaccess,
                },
            ],
        },
        options: {
            responsive: true,
            elements: {
                line: {
                    tension: 0,
                },
                point: {
                    radius: 1,
                    hoverRadius: 3,
                },
            },
            tooltips: {
                mode: "nearest",
                intersect: false,
            },
            title: {
                display: true,
                text: "Medlemsskap",
            },
            scales: {
                xAxes: [
                    {
                        type: "time",
                        time: {
                            parser: timeFormat,
                            // round: 'day'
                            tooltipFormat: "ll",
                            max: maxtime,
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Datum",
                        },
                    },
                ],
                yAxes: [
                    {
                        ticks: {
                            min: 0,
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Antal",
                        },
                    },
                ],
            },
            pan: {
                enabled: true,
                mode: "x",
            },
            zoom: {
                enabled: true,
                mode: "x",
            },
            annotation: {
                events: ["click"],
                annotations: [
                    {
                        drawTime: "afterDatasetsDraw",
                        type: "line",
                        mode: "vertical",
                        scaleID: "x-axis-0",
                        borderColor: "red",
                        borderWidth: 1,
                        value: maxtime,
                    },
                ],
            },
        },
    };

    const memberstats = document.createElement("div") as HTMLDivElement;
    const highestMembership = maxOfSeries(dataMembership) || {
        x: "never",
        y: 0,
    };
    const highestLabaccess = maxOfSeries(dataLabaccess) || { x: "never", y: 0 };

    const today = new Date();
    const currentMembership = pointAtDate(dataMembership, today) || {
        x: today,
        y: 0,
    };
    const currentLabaccess = pointAtDate(dataLabaccess, today) || {
        x: today,
        y: 0,
    };

    memberstats.innerHTML = `
	<canvas width=500 height=300></canvas>
	<div class="statistics-member-stats-box">
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Membership</span><span  class="statistics-member-stats-value">${currentMembership.y
        }</span></div>
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Membership record</span><span  class="statistics-member-stats-value">${highestMembership.y
        } members on ${date2str(highestMembership.x)}</span></div>
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Labaccess</span><span  class="statistics-member-stats-value">${currentLabaccess.y
        }</span></div>
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Labaccess record</span><span  class="statistics-member-stats-value">${highestLabaccess.y
        } members on ${date2str(highestLabaccess.x)}</span></div>
	</div>
	`;
    memberstats.className = "statistics-member-stats";

    const canvas = memberstats.querySelector("canvas")!; // <HTMLCanvasElement>document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    new Chart(ctx, config);

    root.appendChild(memberstats);
}

function addLaserChart(root: HTMLElement, data: any) {
    const maxtime = new Date();

    const config = {
        type: "bar",
        data: {
            datasets: [
                {
                    label: "Laserminuter",
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
                text: "Användning av laserskäraren",
            },
            scales: {
                xAxes: [
                    {
                        type: "time",
                        time: {
                            parser: "YYYY-MM",
                            // round: 'month'
                            tooltipFormat: "ll",
                            unit: "month",
                            max: maxtime,
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Datum",
                        },
                    },
                ],
                yAxes: [
                    {
                        ticks: {
                            min: 0,
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Antal",
                        },
                    },
                ],
            },
        },
    };

    const canvas = document.createElement("canvas") as HTMLCanvasElement;
    root.appendChild(canvas);
    canvas.width = 500;
    canvas.height = 300;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, config);
}

function addMemberDistribution(
    root: HTMLElement,
    data: MemberDistribution,
    description: string,
) {
    let labaccess = data.labaccess;

    // Remove the "wasn't a member during this time" count which will be the data for "0 Months"
    labaccess.splice(0, 1);

    const toPoints = (items: Array<any>) => {
        const values = [];
        for (let i = 0; i < items.length; i++) {
            values.push({ x: "" + (i + 1), y: items[i] });
        }
        return values;
    };

    console.log(toPoints(labaccess));

    const labels = [];
    for (let i = 0; i < labaccess.length; i++) {
        labels.push("" + (i + 1));
    }

    const config = {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Members",
                    backgroundColor: "#FF000077",
                    borderColor: colors[0],
                    fill: false,
                    data: toPoints(labaccess),
                    steppedLine: true,
                },
            ],
        },
        options: {
            title: {
                display: true,
                text: "Active labaccess time over one year.",
            },
            scales: {
                xAxes: [
                    {
                        scaleLabel: {
                            display: true,
                            labelString: "Months",
                        },
                    },
                ],
                yAxes: [
                    {
                        ticks: {
                            min: 0,
                        },
                        scaleLabel: {
                            display: true,
                            labelString: "Member Count",
                        },
                    },
                ],
            },
        },
    };

    const canvas = document.createElement("canvas") as HTMLCanvasElement;
    root.appendChild(canvas);
    canvas.width = 500;
    canvas.height = 300;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, config);

    const desc = document.createElement("p") as HTMLParagraphElement;
    desc.textContent = description;
    root.appendChild(desc);
}

interface Question {
    question: string;
}

interface Option {
    correct: boolean;
    description: string;
}
interface OptionStatistics {
    answer_count: number;
    option: Option;
}

interface QuizStatistics {
    median_seconds_to_answer_quiz: number;
    answered_quiz_member_count: number;
    questions: {
        question: Question;
        options: OptionStatistics[];
        // Number of unique members that have answered this question
        member_answer_count: number;
        incorrect_answer_fraction: number;
    }[];
}

function addQuizChart(root: HTMLElement, data: QuizStatistics, quiz: Quiz) {
    // Sort questions so that the more incorrectly answered questions are at the top
    data.questions.sort(
        (a, b) => b.incorrect_answer_fraction - a.incorrect_answer_fraction,
    );

    // Sort options so that the correct options are to the left.
    for (const q of data.questions) {
        q.options.sort((a, b) => {
            if (a.option.correct != b.option.correct)
                return a.option.correct ? 1 : 0;

            return b.answer_count - a.answer_count;
        });
    }

    // Maximum number of correct and incorrect alternatives for all questions
    const maxCorrect = data.questions
        .map((q) =>
            q.options
                .map<number>((o) => (o.option.correct ? 1 : 0))
                .reduce((a, b) => a + b),
        )
        .reduce((a, b) => Math.max(a, b));
    const maxIncorrect = data.questions
        .map((q) =>
            q.options
                .map<number>((o) => (o.option.correct ? 0 : 1))
                .reduce((a, b) => a + b),
        )
        .reduce((a, b) => Math.max(a, b));

    const correctColors = ["#23851E", "#289622"];
    const incorrectColors = ["#AD2727", "#C82D2D"];

    interface Dataset {
        label: string;
        backgroundColor: string;
        borderColor: string;
        data: any[];
        options: (null | OptionStatistics)[];
    }

    const incorrectDatasets: Dataset[] = [];
    const correctDatasets: Dataset[] = [];

    for (let i = 0; i < maxCorrect; i++) {
        let color = correctColors[Math.min(i, correctColors.length - 1)];
        correctDatasets.push({
            label: "Korrekt",
            backgroundColor: color,
            borderColor: color,
            data: [],
            options: [],
        });
    }
    for (let i = 0; i < maxIncorrect; i++) {
        let color = incorrectColors[Math.min(i, incorrectColors.length - 1)];
        incorrectDatasets.push({
            label: "Inkorrekt",
            backgroundColor: color,
            borderColor: color,
            data: [],
            options: [],
        });
    }

    const datasets = [...correctDatasets, ...incorrectDatasets];

    // Go through each question option and add values to the relevant datasets
    for (let qi = 0; qi < data.questions.length; qi++) {
        const q = data.questions[qi];
        let correct = 0;
        let incorrect = 0;

        for (const o of q.options) {
            let datasetIndex;
            let datasetArray;
            if (o.option.correct) {
                datasetIndex = correct;
                correct++;
                datasetArray = correctDatasets;
            } else {
                datasetIndex = incorrect;
                incorrect++;
                datasetArray = incorrectDatasets;
            }

            console.assert(datasetIndex < datasetArray.length);

            datasetArray[datasetIndex].data.push(
                o.answer_count / q.member_answer_count,
            );
            datasetArray[datasetIndex].options.push(o);
        }

        // Ensure all datasets have the same length to ensure question indices are not messed up.
        for (let i = 0; i < datasets.length; i++) {
            if (datasets[i].data.length <= qi) {
                datasets[i].data.push(0);
                datasets[i].options.push(null);
            }
        }
    }

    const config = {
        type: "horizontalBar",
        data: {
            labels: data.questions.map((q) =>
                q.question.question.substring(
                    0,
                    Math.min(q.question.question.length, 30),
                ),
            ),
            datasets: datasets,
        },
        options: {
            title: {
                display: true,
                text: "Procent rätt på quizfrågor",
            },
            responsive: true,
            scales: {
                xAxes: [
                    {
                        stacked: true,
                    },
                ],
                yAxes: [
                    {
                        stacked: true,
                    },
                ],
            },
            tooltips: {
                format: "nearest",
                position: "nearest",
                callbacks: {
                    title: (tooltipItems: any[], itemData: any) => {
                        return data.questions[tooltipItems[0].index].question
                            .question;
                    },
                    label: (tooltipItem: any, data: any) => {
                        const option =
                            datasets[tooltipItem.datasetIndex].options[
                            tooltipItem.index
                            ];
                        if (option != null) {
                            return (
                                Math.round(
                                    datasets[tooltipItem.datasetIndex].data[
                                    tooltipItem.index
                                    ] * 100,
                                ) +
                                "%: " +
                                option.option.description
                            );
                        } else {
                            return "";
                        }
                    },
                },
            },
        },
    };

    const quizstats = document.createElement("div") as HTMLDivElement;

    quizstats.innerHTML = `
	<h3>Statistics for Quiz: ${quiz.name}</h3>
	<div class="statistics-member-stats-box">
		<div class="statistics-member-stats-row">
			<span class="statistics-member-stats-type">Median time to answer quiz [min]</span>
			<span class="statistics-member-stats-value">${(
            data.median_seconds_to_answer_quiz / 60
        ).toFixed(1)}</span>
		</div>
		<div class="statistics-member-stats-row">
			<span class="statistics-member-stats-type">Total quiz respondents</span>
			<span class="statistics-member-stats-value">${data.answered_quiz_member_count
        }</span>
		</div>
	</div>
	<canvas width=500 height=300></canvas>
	`;
    quizstats.className = "statistics-member-stats";

    const canvas = quizstats.querySelector("canvas")!;
    root.appendChild(quizstats);
    canvas.width = 500;
    canvas.height = 800;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, config);
}

interface Category {
    id: number;
    name: string;
}

interface MemberDistribution {
    membership: number[];
    labaccess: number[];
}

interface ProductStatistics {
    revenue_by_product_last_12_months: {
        product_id: number;
        amount: number;
    }[];
    revenue_by_category_last_12_months: {
        category_id: number;
        amount: number;
    }[];
    products: Product[];
    categories: Category[];
    subscription_split: {
        active_members: number,
        has_membership_sub: number,
        has_makerspace_access_sub: number,
        has_both_subs: number,
    }
}

function addProductPurchasedChart(root: HTMLElement, data: ProductStatistics) {
    const membershipProductIDs: WellKnownProductId[] = [
        "access_starter_pack",
        "single_membership_year",
        "single_labaccess_month",
        "membership_subscription",
        "labaccess_subscription",
    ];
    const onlyMembershipProducts = data.products.filter((p) =>
        membershipProductIDs.some(id => id == p.product_metadata.special_product_id)
    );
    const excludingMembershipProducts = data.products.filter(
        (p) => !membershipProductIDs.some(id => id == p.product_metadata.special_product_id)
    );

    const membershipSales = onlyMembershipProducts.map((p) => ({
        name: p.name,
        amount:
            data.revenue_by_product_last_12_months.find(
                (x) => x.product_id == p.id,
            )?.amount ?? 0,
    }));
    const otherSales = excludingMembershipProducts.map((p) => ({
        name: p.name,
        amount:
            data.revenue_by_product_last_12_months.find(
                (x) => x.product_id == p.id,
            )?.amount ?? 0,
    }));

    membershipSales.push({
        name: "Other products",
        amount: otherSales.map((x) => x.amount).reduce((a, b) => a + b),
    });

    addRevenueChart(
        root,
        membershipSales,
        "Försäljning i webshoppen av medlemskap (senaste 12 månaderna)",
    );
    addRevenueChart(
        root,
        otherSales,
        "Försäljning i webshoppen av övriga produkter (senaste 12 månaderna)",
    );
    addRevenueChart(
        root,
        data.categories.map((c) => ({
            name: c.name,
            amount:
                data.revenue_by_category_last_12_months.find(
                    (x) => x.category_id == c.id,
                )?.amount ?? 0,
        })),
        "Försäljning i webshoppen per kategori (senaste 12 månaderna)",
    );
}

function addRevenueChart(
    root: HTMLElement,
    data: { name: string; amount: number }[],
    label: string,
) {
    // Sort by sales
    data.sort((a, b) => b.amount - a.amount);

    const config = {
        type: "horizontalBar",
        data: {
            labels: data.map((x) => x.name),
            datasets: [
                {
                    label: "Revenue",
                    backgroundColor: "#FF000077",
                    borderColor: colors[0],
                    data: data.map((x) => x.amount),
                },
            ],
        },
        options: {
            title: {
                display: true,
                text: label,
            },
            scales: {
                xAxes: [
                    {
                        stacked: true,
                    },
                ],
                yAxes: [
                    {
                        stacked: true,
                    },
                ],
            },
            tooltips: {
                mode: "nearest",
                intersect: false,
            },
        },
    };

    const canvas = document.createElement("canvas") as HTMLCanvasElement;
    root.appendChild(canvas);
    canvas.width = 500;
    canvas.height = 70 + 30 * data.length;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, config);
}

type Node = { id: number; name: string; color?: string };
type Link = { source: number; target: number; value: number; pause: boolean };
type RetentionGraph = {
    nodes: Node[];
    links: Link[];
};
async function addRetentionChart(root: HTMLElement, graph: RetentionGraph) {
    // set the dimensions and margins of the graph
    var margin = { top: 10, right: 10, bottom: 10, left: 10 },
        width = 1600 - margin.left - margin.right,
        height = 1000 - margin.top - margin.bottom;

    // append the svg object to the body of the page
    var svg = d3
        .select(root)
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("style", "max-width: unset;")
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Color scale used
    var color = d3.scaleOrdinal(d3.schemeCategory10);

    // Set the sankey diagram properties
    var sankeyF = sankey<Node, Link>()
        .nodeWidth(36)
        .nodePadding(50)
        .size([width, height])
        .nodeAlign(sankeyLeft);

    console.log(sankeyF);

    // Constructs a new Sankey generator with the default settings.
    sankeyF
        .nodeId((d) => d.id)
        .nodes(graph.nodes)
        .links(graph.links);

    for (const node of graph.nodes) {
        node.color = color(node.name.replace(/ .*/, ""));
    }

    const generated = sankeyF(graph);

    console.log(generated.nodes);
    console.log(generated.links);

    // add in the links
    // var link = svg.append("g")
    // .selectAll(".link")
    // .data(graph.links)
    // .enter()
    // .append("path")
    // .attr("class", "link")
    // .attr("d", sankeyF.link() )
    // .style("stroke-width", d => Math.max(1, d.dy))
    // .sort((a, b) => b.dy - a.dy);
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#000")
        .attr("stroke-opacity", 0.2)
        .selectAll("path")
        .data(generated.links)
        .join("path")
        .attr("d", sankeyLinkHorizontal())
        .attr("stroke-width", (d) => Math.max(1, d.width!))
        .attr("stroke", (d) => (d.pause ? "red" : "black"));

    // add in the nodes
    const node = svg
        .append("g")
        .selectAll(".node")
        .data(generated.nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .attr("transform", (d) => `translate(${d.x0!},${d.y0!})`);
    // .call(d3.drag()
    // 	.subject(d => d)
    // 	.on("start", function() { this.parentNode.appendChild(this); })
    // 	.on("drag", dragmove));

    // add the rectangles for the nodes

    node.append("rect")
        .attr("height", (d) => d.y1! - d.y0!)
        .attr("width", sankeyF.nodeWidth())
        .style("fill", (d) => d.color!)
        .style("stroke", (d) => d3.rgb(d.color!).darker(2).formatRgb())
        // Add hover text
        .append("title")
        .text(
            (d) => d.name + "\n" + "There is " + d.name + " stuff in this node",
        );

    // add in the title for the nodes
    node.append("text")
        .attr("x", (d) => -0.5 * (d.x1! - d.x0!))
        .attr("y", (d) => d.height! / 2)
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .attr("transform", null)
        .text((d) => d.name)
        .filter((d) => d.x0! < width / 2)
        .attr("x", 6 + sankeyF.nodeWidth())
        .attr("text-anchor", "middle");

    // the function for moving the nodes
    // function dragmove(d) {
    // d3.select(this)
    // .attr("transform",
    // 		"translate("
    // 		+ d.x + ","
    // 		+ (d.y = Math.max(
    // 			0, Math.min(height - d.dy, d3.event.y))
    // 			) + ")");
    // sankeyF.relayout();
    // link.attr("d", sankeyF.link() );
    // }
}
