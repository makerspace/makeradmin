const path = require('path');
const merge = require('webpack-merge');
const webpack = require('webpack');

module.exports = (env, args) => {
    let src = path.resolve(__dirname, "src");
    
    // Get git info from command line
    let commitHash = require("child_process")
        .execSync("sh -c 'find " + src + " -type f -exec md5sum {} \\; | sort -k 2 | md5sum'")
        .toString();
    
    // Get the build date
    let options = {
        year: 'numeric', month: 'numeric', day: 'numeric',
        hour: 'numeric', minute: 'numeric', second: 'numeric',
        hour12: false
    };
    let buildDate = new Intl.DateTimeFormat('sv-SE', options).format(new Date());
    
    const commonSettings = {
        context: src,
        entry: "./app.jsx",
    
        // Compile into a js.app
        output:
        {
        filename: "app.js",
            publicPath: "js",
        path: path.resolve(__dirname, "dist/js"),
        },
        
        // Preprocess *.jsx files
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    exclude: /node_modules/,
                    use: ['babel-loader'],
                },
                {
                    test: /\.css$/,
                    use: [
                        {
                            loader: "style-loader",
                            options: {
                                sourceMap: true
                            }
                        },
                        {
                            loader: "css-loader",
                            options: {
                                sourceMap: true
                            }
                        }
                    ]
                },
            ]
        },
    
        // Files to include.
        resolve: {
            extensions: ['*', '.js', '.jsx']
        },
    
        // Include build information (build date, git hash)
        plugins: [
            new webpack.DefinePlugin({
                __COMMIT_HASH__: JSON.stringify(commitHash),
                __BUILD_DATE__: JSON.stringify(buildDate),
            })
        ],
    };
    
    if (args.mode === "development") {
        console.info("webpack development mode");
    
        return merge(commonSettings, {
            mode: "development",
            devtool: "inline-source-map",
            plugins: [
            ],
            devServer: {
                host: "0.0.0.0",
                port: "80",
                contentBase: "./dist",
                historyApiFallback: true,
                public: 'http://localhost:8009',
            },
        });
    }
    
    console.info("webpack production mode");

    const UglifyJsPlugin = require('uglifyjs-webpack-plugin');
    const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

    return merge(commonSettings, {
        mode: "production",
        devtool: "source-map",
        plugins: [
            new webpack.LoaderOptionsPlugin({
                minimize: true,
            }),
            // new BundleAnalyzerPlugin(),
        ],
    });
};
