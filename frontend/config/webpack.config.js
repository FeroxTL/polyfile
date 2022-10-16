const path = require('path');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const BundleTracker = require('webpack-bundle-tracker');


const rootDir = path.resolve(__dirname, '..');
const mainAppDir = path.resolve(rootDir, '..', 'polyfile');
const bundlesDir = path.resolve(mainAppDir, 'web_dev_assets', 'bundles');
const srcDir = path.resolve(rootDir, 'src');


var config = {
  context: __dirname,
  entry: {
    dashboard: {
      import: path.resolve(srcDir, 'index.js'),
      dependOn: 'vendor',
    },
    vendor: [path.resolve(srcDir, 'styles/style.scss')],
    blockForm: [path.resolve(srcDir, 'styles/block-form.css')],
  },
  output: {
    path: bundlesDir,
    filename: "[name]-[fullhash].js",
    clean: true,
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: 'static/css/[name].[contenthash].css',
      linkType: "text/css",
    }),
    new BundleTracker({filename: path.resolve(mainAppDir, 'webpack-stats.json')}),
  ],
  module: {
    rules: [
      {
        test: /\.(scss|css)$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/img/[hash][ext][query]'
        }
      },
      {
        test: /\.(svg|eot|woff|woff2|ttf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/fonts/[hash][ext][query]'
        }
      },
    ],
  },
};


module.exports = (env, argv) => {
  if (argv.mode === 'development') {
    config.devtool = 'source-map';
  }

  if (argv.mode === 'production') {
    //...
  }

  return config;
};
