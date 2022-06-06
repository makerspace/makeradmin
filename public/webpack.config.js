const path = require('path');
const merge = require('webpack-merge');
const webpack = require('webpack');

module.exports = (env, args) => {
    const commonSettings = {
        context: path.resolve(__dirname),
        entry: {
            receipt: "./ts/receipt.ts",
            shop: "./ts/shop.ts",
            cartpage: "./ts/cartpage.ts",
            cart: "./ts/cart.ts",
            category: "./ts/category.ts",
            register: "./ts/register.ts",
            product: "./ts/product.ts",
            history: "./ts/history.ts",
            member: "./ts/member.ts",
            statistics: "./ts/statistics.ts",
            quiz: "./ts/quiz.tsx",
            licenses: "./ts/licenses.ts",
            courses: "./ts/courses.ts",
        },
        
        output:
            {
                filename: "[name].js",
                path: path.resolve(__dirname, "static/js"),
            },
        
        module: {
            rules: [
                {
                    test: /\.(ts|tsx)$/,
                    exclude: /node_modules/,
                    use: ['ts-loader'],
                },
            ]
        },
        
        resolve: {
            extensions: ['*', '.ts', '.tsx', '.js']
        },
        
        plugins: [
        ],
    };
    
    if (args.mode === 'development') {
        console.info("webpack development mode");
        
        return merge(commonSettings, {
            mode: "development",
            devtool: "inline-source-map",
            plugins: [
            ],
            devServer: {
                host: "0.0.0.0",
                port: 80,
                public: 'http://localhost:8011',
                publicPath: '/static/js',
                proxy: {
                    '/': 'http://localhost:81',
                    '/member': 'http://localhost:81',
                    '/shop': 'http://localhost:81',
                }
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

