const path = require('path');
const merge = require('webpack-merge');
const webpack = require('webpack');

const commonSettings = {
    context: path.resolve(__dirname),
    entry: {
        receipt: "./ts/receipt.ts",
        shop: "./ts/shop.ts",
        cartpage: "./ts/cartpage.ts",
        cart: "./ts/cart.ts",
        category: "./ts/category.ts",
        register: "./ts/register.ts",
        product_edit: "./ts/product_edit.ts",
        product: "./ts/product.ts",
        history: "./ts/history.ts",
        member: "./ts/member.ts",
        statistics: "./ts/statistics.ts",
    },

    // Compile into a js.app
    output:
    {
        filename: "[name].js",
        path: path.resolve(__dirname, "dist"),
    },
    
    // Preprocess *.jsx files
    module: {
        rules: [
            {
                test: /\.(ts)$/,
                exclude: /node_modules/,
                use: ['ts-loader'],
            },
        ]
    },

    // Files to include.
    resolve: {
        extensions: ['*', '.ts', '.tsx']
    },

    plugins: [
    ],
};


// if (process.env.DEVELOPMENT) {
//     console.info("webpack development mode");
//
//     module.exports = merge(commonSettings, {
//         mode: "development",
//         devtool: "inline-source-map",
//         plugins: [
//         ],
//         devServer: {
//             host: "0.0.0.0",
//             contentBase: "./dist",
//             historyApiFallback: true,           
//         },
//     });
// }
// else {
//     console.info("webpack production mode");
//
//     const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
//     const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
//    

    module.exports = merge(commonSettings, {
        mode: "production",
        devtool: "source-map",
        plugins: [
            // new webpack.LoaderOptionsPlugin({
            //     minimize: true,
            // }),
            // // new BundleAnalyzerPlugin(),
        ],
    });
//}
