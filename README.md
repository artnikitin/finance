# CS50 Finance (stock yield)

Implementation of Harvard's [CS50](https://cs50.harvard.edu)'s finance problem set. You can buy and sell stocks (sort of) and manage a portfolio. I've added a feature, that shows stock yield: how much you've earned (in %) from the time you've purchased the stocks. The interest is calculated for each transaction (one stock or a bundle).
For selling stocks you may choose 3 different algorithms, all of which are present in the profile settings:

* FIFO (first in first out)
* LIFO (last in first out)
* MARGIN (sell the most profitable stocks first)

## Academic Honesty

If you're a CS50's student and not yet solved the problem set, be reasonable and don't browse and use this code in your assignments. My [certificate](https://courses.edx.org/certificates/e7ebacc2c4da4560abbc24e87e29e396) for motivation. Others interested are welcome.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Be sure to install Python3. For other modules and libraries run:

```
$ pip install -r requirements.txt
```

### Installing

Download the repository manually or run:

```
$ git clone https://github.com/artnikitin/finance.git
$ cd finance
$ export FLASK_APP=application.py
$ flask run
```

## Usage

Register and login as a new user. Check for stock prices in quote. Be sure to use stock symbols as GOOG, APPL, FB, NFLX etc. Buy and sell stocks through the links. View transactions on history page.

Portfolio has yield counter in %:

![Alt text](examples/finance_portfolio.jpeg?raw=true)

Choose selling algorithm in profile settings:

![Alt text](examples/finance_profile.jpeg?raw=true)

## API

By default stocks data is downloaded from [Yahoo Finance](https://finance.yahoo.com), but it looks like they're not supporting the service anymore. Alternative source is [Alpha Vantage](https://www.alphavantage.co).

## Built With

* Flask
* SQLAlchemy (CS50's library)
* SQLite3

## Authors

* CS50 staff
* **Tim Nikitin** - problem set, yield and selling algorithms - [artnikitin](https://github.com/artnikitin)

## License

This project is licensed under the MIT License - see the [LICENSE.md](/LICENSE.md) file for details

