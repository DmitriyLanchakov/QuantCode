from datahandler import DataHandler
import os, time

class Backtest(object):

    def __init__(self, strategy, portfolio, analyser, **kwargs):
        self.strategy = strategy
        self.portfolio = portfolio
        self.analyser = [analyser] if type(analyser) != list else analyser
        self.backtest_modules = [self, self.strategy, self.portfolio]
        self.backtest_modules.extend(self.analyser)

        self.symbols = None
        self.qcodes = None
        self.date_start = None
        self.date_end = None
        self.frequency = None
        self.datas = None
        self.trade_time = None
        self.benchmark = None
        self.benchmark_qcode = None

        for module in self.backtest_modules:
            module.__dict__.update(kwargs)
        #self.__dict__.update(kwargs)

        self.validate_input()
        self.create_outdir()

        self.data_handler = DataHandler(self.symbols, self.qcodes, self.date_start, self.date_end, self.frequency, self.datas)
        self.benchmark_handler = DataHandler([self.benchmark], [self.benchmark_qcode], self.date_start, self.date_end, self.frequency, self.datas)

    def validate_input(self):
        if self.symbols is None:
            raise ValueError, "Need to choose symbols to trade"

        if self.benchmark is None:
            print "No benchmark specified. Default is SPY"
            self.benchmark = 'SPY'
            self.benchmark_qcode = 'GOOG/NYSE_SPY'

    def create_outdir(self):
        outdir = self.options.outdir

        if self.options.save:
            date = time.strftime("%Y_%m_%d")
            outdirbase = os.path.join(self.options.outdir, date)
            revision = 1
            while os.path.exists(outdir):
                outdir = outdirbase + "_" + str(revision)
                revision += 1

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        for module in self.backtest_modules:
            module.outdir = outdir

    def run(self):
        print "\n\nHandling data"
        datas_symbols = self.data_handler.generate_data()
        datas_benchmark = self.benchmark_handler.generate_data()
        for module in self.backtest_modules:
            module.datas_symbols = datas_symbols
            module.datas_benchmark = datas_benchmark
            module.prices = datas_symbols[self.trade_time]
            module.prices_bm = datas_benchmark[self.trade_time]
        
        print "\n\nGenerating signals"
        self.strategy.begin()
        self.strategy.generate_signals()
        for module in self.backtest_modules:
            module.__dict__.update(self.strategy.__dict__)
        
        print "\n\nBacktesting portfolio"
        self.portfolio.begin()
        self.portfolio.generate_returns()
        for module in self.backtest_modules:
            module.__dict__.update(self.portfolio.__dict__)

        print "\n\nAnalysing results"
        for analyser in self.analyser:
            analyser.begin()
            analyser.generate_analysis()
