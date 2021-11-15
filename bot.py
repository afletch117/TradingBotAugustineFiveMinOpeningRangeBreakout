class AugustineFiveMinOpeningRangeBreakout(QCAlgorithm):
    
    ## Just Reduced Log Limit to 10M / Day.  
    ## I need to Limit the Log to only what is necessary
    
    min_entry_price= 2
    max_entry_price = 10
    
    min_float = 1000000
    max_float = 100000000
    
    min_gap_percentage = 1.04
    min_premarket_volume = 50000
    min_price_action_vs_gap_percentile_at_open = 0.5
    
    max_price_filtered_securities = 2000    ## Should be >= max_float_filtered_securities
    max_float_filtered_securities = 2000      ## ¿Max Universe Size 100 - 1000?
    
    

    def Initialize(self):
        self.SetStartDate(2020, 4, 7)
        self.SetEndDate(2020, 4, 7)
        self.SetCash(100000)
        
        self.UniverseSettings.Resolution = Resolution.Minute
        self.UniverseSettings.ExtendedMarketHours = True
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        
        self.SetTimeZone("America/New_York")
        
        self.midnight_watchlist = []
        self.opening_watchlist = []
        self.orb_candidates = []
        ##self.opening_range_breakouts = []
        
        self.todays_opening_prices = {}
        self.yesterdays_closing_prices = {}
        self.premarket_volumes = {}
        self.premarket_highs = {}
        self.breakout_prices = {}
        self.indicators = {}


    def CoarseSelectionFunction(self, coarse):
        coarse_selected = []
        coarse_selected_values = []
        
        # Consider Sorting by Lowest Price first to incline Universe towards Lower Priced Stocks
        filtered_by_price = [c for c in coarse if (self.min_entry_price < c.Price < self.max_entry_price)][:self.max_price_filtered_securities]
        
        for c in filtered_by_price:
            self.yesterdays_closing_prices[c.Symbol] = c.Price
            coarse_selected.append(c.Symbol)
            coarse_selected_values.append(c.Symbol.Value)
            
        count_coarse_selected_securities = len(coarse_selected)
        
        ## DEBUG LOG - Remove for Live Trading
        #self.Debug(f' --- DEBUG --- Coarse Selected Securities: {coarse_selected_values} --- DEBUG --- ')
        #self.Debug(f' --- DEBUG --- Coarse Selected Count: {count_coarse_selected_securities} --- DEBUG --- ')
        self.Log(f' --- DEBUG --- Coarse Selected Securities: {coarse_selected_values} --- DEBUG --- ')
        self.Log(f' --- DEBUG --- Coarse Selected Count: {count_coarse_selected_securities} --- DEBUG --- ')
        
        
        return coarse_selected 
    
    
    def FineSelectionFunction(self, fine):
        fine_selected = []
        #fine_selected_values = []
        ## Sort by float, smallest to largest
        sorted_by_float = sorted(fine, key=lambda f: f.CompanyProfile.SharesOutstanding)    
        for f in sorted_by_float:
            if (self.min_float < f.CompanyProfile.SharesOutstanding < self.max_float):
                fine_selected.append(f.Symbol)
                #fine_selected_values.append(f.Symbol.Value)
                ## DEBUG LOG - Remove for Live Trading
                #self.Log(f' --- DEBUG --- Float Stock: {f.Symbol.Value}, Float: {f.CompanyProfile.SharesOutstanding} --- DEBUG ---' )
        
        #count_fine_selected = len(fine_selected)
        
        
        #self.Debug(f'Midnight Watchlist: {fine_selected_values}')
        #self.Debug(f'Midnight Watchlist Count: {count_fine_selected}')
        #self.Log(f'Midnight Watchlist: {fine_selected_values}')
        #self.Log(f'Midnight Watchlist Count: {count_fine_selected}')
        
        return fine_selected[:self.max_float_filtered_securities]
        
        
    def OnSecuritiesChanged(self, changes):
        if self.Time.hour == 0 and self.Time.minute == 00:
            for security in changes.AddedSecurities:
                symbol = security.Symbol
                self.Securities[symbol].SetDataNormalizationMode(DataNormalizationMode.Adjusted)
                self.midnight_watchlist.append(symbol)
                
                #history = self.History(symbol, 270, Resolution.Daily)
                
                self.indicators[symbol] = DailyWarmup()
                
                self.indicators[symbol].vwap = self.VWAP(symbol, 390, Resolution.Minute)
                #self.indicators[symbol].atr = self.ATR(symbol, 14, MovingAverageType.Simple, Resolution.Daily)
                
                #for bar in history.itertuples():
                    #tradebar = TradeBar(bar.Index[1], symbol, bar.open, bar.high, bar.low, bar.close, bar.volume)
                    #self.indicators[symbol].atr.Update(tradebar)
                    #self.indicators[symbol].vwap.Update(tradebar)
            
            self.Log(f'Midnight Watchlist: {[x.Value for x in self.midnight_watchlist]}')
            self.Log(f'Midnight Watchlist Count: {len(self.midnight_watchlist)}')


    def OnData(self, data):
        
        ## Premarket Data
        if self.Time.hour == 9 and self.Time.minute <= 30 or 4 <= self.Time.hour < 9:
            for i in self.midnight_watchlist:
                if data.ContainsKey(i):
                    ticker = i.Value        ## Accesses Symbol's Ticker, "i" accesses the Symbol Object
                    symbol_volume = data[i].Volume
                    symbol_high = data[i].High
                    
                    ## -- DEBUG --, Remove for Live Trading
                    #self.Debug(f" -- DEBUG -- PREMARKET VOLUME Received for {ticker}: {symbol_volume} -- DEBUG --")
                    #self.Log(f" -- DEBUG -- PREMARKET Data Received for {ticker}, High: {symbol_high}, Volume: {symbol_volume} -- DEBUG --")
                    
                    if i in self.premarket_volumes:
                        if symbol_volume > 0:  # Why non-negative?
                            self.premarket_volumes[i] += symbol_volume
                            #self.Debug(f' --- DEBUG --- {self.Time} Premarket Vomlue for {i}: {self.premarket_volumes[i]}  --- DEBUG --- ')
                            #self.Log(f' --- DEBUG --- Premarket Volume for {ticker}: {self.premarket_volumes[i]}  --- DEBUG --- ')
                        
                    if i not in self.premarket_volumes:
                        self.premarket_volumes[i] = symbol_volume
                        #self.Debug(f' --- DEBUG --- {self.Time} Premarket Volume for {i}: {self.premarket_volumes[i]}  --- DEBUG --- ')
                        #self.Log(f' --- DEBUG --- Premarket Volume for {ticker}: {self.premarket_volumes[i]}  --- DEBUG --- ')
                     
                        
                    if i in self.premarket_highs:
                        if symbol_high > self.premarket_highs[i]:
                            self.premarket_highs[i] = symbol_high
                            #self.Debug(f' --- DEBUG --- Premarket High for {i}: {self.premarket_highs[i]}  --- DEBUG --- ')
                            #self.Log(f' --- DEBUG --- Premarket High for {ticker}: {self.premarket_highs[i]}  --- DEBUG --- ')
                        
                    if i not in self.premarket_highs:
                        self.premarket_highs[i] = symbol_high
                        #self.Debug(f' --- DEBUG --- Premarket High for {i}: {self.premarket_highs[i]}  --- DEBUG --- ')
                        #self.Log(f' --- DEBUG --- Premarket High for {ticker}: {self.premarket_highs[i]}  --- DEBUG --- ')
                  
                 
        ## Opening Data
        if self.Time.hour == 9 and self.Time.minute == 31:
            for i in self.midnight_watchlist:
                if data.ContainsKey(i):
                    ticker = i.Value        ## Accesses Symbol's Ticker, "i" accesses the Symbol Object
                    
                    self.todays_opening_prices[i] = data[i].Open
                        
                    ## -- Next, Remove securities from Trading Universe that do not meet Gap Percentage,
                    ## Premarket Volume, and Price Action requirements,
                    ## and add the securities remaining to self.opening_watchlist, Debug-Log to verify
                     
                    ## Filter Universe for Gap Percentage
                    gap_open = self.yesterdays_closing_prices[i]
                    gap_close = data[i].Open
                    gap_percentage = gap_close / gap_open
                        
                    if gap_percentage >= self.min_gap_percentage:
                        gap_filter_pass = True
                            
                    else:
                        gap_filter_pass = False
                        
                    ## -- DEBUG --, Remove for Live Trading
                    #self.Debug(f" -- DEBUG -- Gap Percentage: {ticker}, {gap_percentages[i]} -- DEBUG --")
                    #self.Debug(f" -- DEBUG -- Gap Filter Pass?: {gap_filter_pass} -- DEBUG --")
                    #self.Log(f" -- DEBUG -- Gap Percentage: {ticker}, {gap_percentages[i]} -- DEBUG --")
                    #self.Log(f" -- DEBUG -- Gap Filter Pass?: {gap_filter_pass} -- DEBUG --")
                                
                    
                    if i in self.premarket_volumes and i in self.premarket_highs:            
                        premarket_volume = self.premarket_volumes[i]
                        premarket_high = self.premarket_highs[i]
                            
                        if premarket_volume >= self.min_premarket_volume:
                            premarket_volume_filter_pass = True
                                
                        else:
                            premarket_volume_filter_pass = False
                            
                        ## Price Action must be in the top 50% of the Gap range at Market Open.
                        price_action_threshold = ((premarket_high - gap_open) * self.min_price_action_vs_gap_percentile_at_open) + gap_open
                            
                        if gap_close >= price_action_threshold:
                            price_action_filter_pass = True
                            
                        else:
                            price_action_filter_pass = False
                            
                        ## -- DEBUG --, Remove for Live Trading
                        #self.Debug(f" -- DEBUG -- Symbol: {ticker}, Gap Percentage : {gap_percentages[i]}, Premarket Volume: {premarket_volume}, Premarket High: {premarket_high}, Gap Open: {gap_open}, Gap Close: {gap_close} -- DEBUG --")
                        #self.Debug(f" -- DEBUG -- {ticker} Gap Filter Pass: {gap_filter_pass}, Premarket Volume Pass: {premarket_volume_filter_pass}, Price Action Pass: {price_action_filter_pass}  -- DEBUG --")
                        self.Log(f" -- DEBUG -- Symbol: {ticker}, Gap Percentage : {gap_percentage}, Premarket Volume: {premarket_volume}, Premarket High: {premarket_high}, Gap Open: {gap_open}, Gap Close: {gap_close} -- DEBUG --")
                        self.Log(f" -- DEBUG -- {ticker} Gap Filter Pass: {gap_filter_pass}, Premarket Volume Pass: {premarket_volume_filter_pass}, Price Action Pass: {price_action_filter_pass}  -- DEBUG --")
                            
                        if gap_filter_pass and premarket_volume_filter_pass and price_action_filter_pass:
                            self.opening_watchlist.append(i)
                            #opening_watchlist_values.append(ticker)
                            
                        
                    
            #self.Debug(f"Opening Watchlist: {opening_watchlist_values}")
            #self.Debug(f"Opening Watchlist Count: {opening_watchlist_count}")
            self.Log(f"Opening Watchlist: {[x.Value for x in self.opening_watchlist]}")
            self.Log(f"Opening Watchlist Count: {len(self.opening_watchlist)}")
            
            
            ## ------ BOOKMARK ------
            ## ------ BOOKMARK ------
            ## Warmup Daily 200 EMA, ATR, VWAP, and Daily Resistance Levels
            for i in self.opening_watchlist:
                history = self.History(i, 270, Resolution.Daily)
                
                self.indicators[i].ema = self.ema = ExponentialMovingAverage(i, 200)
                self.indicators[i].atr = self.ATR(i, 14, MovingAverageType.Simple, Resolution.Daily)
                
                for bar in history.itertuples():
                    tradebar = TradeBar(bar.Index[1], i, bar.open, bar.high, bar.low, bar.close, bar.volume)
                    self.indicators[i].ema.Update(bar.Index[1], bar.close)
                    self.indicators[i].atr.Update(tradebar)
                    
                    #self.Plot('Opening Watchlist VWAP by Symbol', i.Value, self.indicators[i].vwap.Current.Value)
                
                
                self.Log(f"Indicators for {i.Value}: 200 EMA: {self.indicators[i].ema}, 14-Day ATR: {self.indicators[i].atr}, VWAP: {self.indicators[i].vwap}")
                #self.Log(f"Opening VWAP for {i.Value}: {self.indicators[i].vwap}")
                
                
        
        ## End of 5 minute Opening Range, ORB Candidates list & Consolidator Creation
        #if self.Time.hour == 9 and self.Time.minute == 35:
            #for i in self.opening_watchlist:
                #if data.ContainsKey(i):
                    
                    
                    ## ------ BOOKMARK ------
                    ## Working on 5 min Consolidator --
                    ## Save the Breakout Price and Filter for Positive ORB, ORB to ATR Ratio,
                    ## and Reward to Risk Ratio.  Then, Create and subscribe to a 5 min Conoslidator
                    
                    #if positive_orb_pass and orb_to_atr_ratio_pass and reward_risk_ratio_pass:
                        #self.orb_candidates.append(i)
                        # five_minute_consolidator = TradeBarConsolidator(i, timedelta(minutes=5))
                        # five_minute_consolidator.DataConsolidated += self.FiveMinuteBarHandler
                        # self.SubscriptionManager.AddConsolidator(i, five_minute_consolidator)
                 
                    
        ## Buying Period, between 9:36 and 9:59
        #if self.Time.hour == 9 and 36 <= self.Time.minute <= 59:
            #for i in self.orb_candidates:
                #if data.ContainsKey(i):
                    ## If the High for a security breaks it's Breakout Price
                    ## and still meets Reward Risk requirements: 
                        ## Buy the Security with a Stop and Limit Order
                        ## set according to Profit Target Rules
                        ## Also, remove security from self.orb_candidates,
                        ## and add it to self.orpening_range_breakouts
            
            
            
        ## Intraday Data
        if self.Time.hour == 9 and self.Time.minute > 36 or 9 < self.Time.hour < 16:
            #for i in self.opening_watchlist:    # Eventually change to orb_candidates and opening_range_breakouts
                #self.Plot('Opening Watchlist VWAP by Symbol', i.Value, self.indicators[i].vwap.Current.Value)
                
          
            
            for i in self.orb_candidates:
                if data.ContainsKey(i):
                    symbol = data.Bars.i.Key      ## Accesses i's Symbol
                    value = data.Bars.i.Value
                        
                    ## -- DEBUG --, Remove for Live Trading
                    #self.Debug(f" -- DEBUG -- Intraday Data Received for: {symbol.Value} -- DEBUG --")
                    #self.Log(f" -- DEBUG -- Intraday Data Received for: {symbol.Value} -- DEBUG --")
                    
                    
    #def FiveMinuteBarHandler(self, five_minute_consolidator, bar):
        #for i in self.opening_range_breakouts:
            ## if i is contained in bar:
                ## if we own i:
                    ## if VWAP is ready, and the New 5 minute bar closes below the VWAP:
                        ## Liquidate the Security
                    
                    ## if the Profit Target is None:
                        ## reset the Stop Sell Price to the Low of the New 5 min Bar
                        
class DailyWarmup():
    def __init__(self):
        return
        #self.ema = ExponentialMovingAverage(200)

        #for bar in history.itertuples():
            #self.ema.Update(bar.Index[1], bar.close)
           


        ## Warmup Daily Resistance Levels
        ## ¿Warmup VWAP here, or in OnData after Opening Watchlist creation?
