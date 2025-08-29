const path = require("path");
const { merge } = require("webpack-merge");
const webpack = require("webpack");

module.exports = (env, args) => {
    watch_or_server_mode = !!env["WEBPACK_WATCH"] || !!env["WEBPACK_SERVE"];

    const commonSettings = {
        context: path.resolve(__dirname),
        entry: {
            receipt: "./ts/receipt.tsx",
            shop: "./ts/shop.tsx",
            cartpage: "./ts/cartpage.tsx",
            cart: "./ts/cart.ts",
            category: "./ts/category.ts",
            register: "./ts/register.tsx",
            product: "./ts/product.ts",
            history: "./ts/history.tsx",
            member: "./ts/member.tsx",
            statistics: "./ts/statistics.ts",
            quiz: "./ts/quiz.tsx",
            licenses: "./ts/licenses.tsx",
            courses: "./ts/courses.tsx",
            reset_password: "./ts/reset_password.tsx",
        },

        output: {
            filename: "[name].js",
            publicPath: "/static/js/",
            path: path.resolve(__dirname, "static/js"),
        },

        module: {
            rules: [
                {
                    test: /\.(ts|tsx)$/,
                    exclude: /node_modules/,
                    use: ["ts-loader"],
                },
            ],
        },

        resolve: {
            extensions: ["*", ".ts", ".tsx", ".js"],
            alias: {
                react: "preact/compat",
                "react-dom": "preact/compat",
            },
        },

        plugins: [],

        stats: watch_or_server_mode ? "errors-warnings" : "normal",
    };

    if (args.mode === "development") {
        console.info("webpack development mode");

        return merge(commonSettings, {
            mode: "development",
            devtool: "inline-source-map",
            plugins: [],
            devServer: {
                host: "0.0.0.0",
                allowedHosts: "all",
                port: 80,
                static: "/static/js",
                proxy: {
                    "/": "http://localhost:81",
                    "/member": "http://localhost:81",
                    "/shop": "http://localhost:81",
                },
            },
            infrastructureLogging: {
                level: "error",
            },
        });
    }

    console.info("webpack production mode");

    return merge(commonSettings, {
        mode: "production",
        devtool: "source-map",
        plugins: [
            new webpack.LoaderOptionsPlugin({
                minimize: true,
            }),
        ],
    });
};
