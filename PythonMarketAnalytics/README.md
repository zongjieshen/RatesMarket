# Interest Rates Market Add-in

## Description

* The package uses Scipy for Newton-Raphson optimization.
* A multiprocessing framework is also embedded to speed up the market building process
* It also provides the flexiblity for users to choose which instruments to use in the curve building process

## Installing the Package
The package is not on pip at the moment, user need to clone the repo and install locally
```
pip install -e C:\Users\Zongjie\source\repos\zongjieshen\RatesMarket\PythonMarketAnalytics
```
**_NOTE:_** Replace the repo directory with your own

### Dependencies

* Dependecies are all defined in the ```requirement.txt``` file

### Executing program
1. Any Jupter Notebook should be able to import the package installed locally
2. A Spreadsheet 'MarketAddin.xlsm' with xlwings added-in is also attached (You need to install xlwings add-in and Enable xlwings references in VBA, more details at https://docs.xlwings.org/en/stable/udfs.html)

After installing the package, you can import the package as a standard one
#####Notebook
```
Import Market as mkt
import pandas as pd
valueDate = pd.to_datetime('31/12/2021',format = '%d/%m/%Y')
baseMarket = mkt.Create('baseMarket',valueDate)
baseMarket.GetItems()
```
![](2022-05-16-13-31-51.png)
#####Excel
In Excel after the xlwings Ribbon is loaded, click Import functions and type the formula
```
=MarketCreate("baseMarket",valueDate,,buildItems)
==MarketItems(marketHandle)
```
![](2022-05-16-13-28-38.png)
![](2022-05-16-13-28-14.png)
**_NOTE:_** In the sample spreadsheet, buildItems is an Excel range and user can define the Curve params.
![](2022-05-16-13-30-25.png)

More useages are defined in the wiki section

## Version History
* 0.1
    * Initial Release

## License

This project is licensed under the [MIT] License

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)