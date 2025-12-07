//+------------------------------------------------------------------+
//| AIBridge_EA.mq4                                                 |
//| Example MQL4 Expert Advisor template that sends recent candles  |
//| to a Python ZeroMQ server and executes signals returned.        |
//| NOTE: You need a ZeroMQ MQL4 wrapper (mql4-zmq) and the DLL.    |
//+------------------------------------------------------------------+

#property strict
#property version   "1.0"

// Include ZeroMQ wrapper header here (from mql4-zmq or similar)
// #include <zmq.mqh>

input string ServerHost = "127.0.0.1";
input int    ServerPort = 5555;
input int    WindowBars = 40; // number of recent bars to send
input double RiskPercent = 1.0; // percent of account per trade

int OnInit()
{
   // Initialize ZMQ socket here using the wrapper
   // Example (pseudocode):
   // if(!ZmqInit()) { Print("ZMQ init failed"); return(INIT_FAILED); }
   // ZmqConnect("tcp://" + ServerHost + ":" + IntegerToString(ServerPort));
   Print("AIBridge_EA initialized - ensure mql4-zmq wrapper is installed and configured.");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   // Clean up ZMQ
}

void OnTick()
{
   static datetime lastTime=0;
   if(Time[0]==lastTime) return; // already processed this tick
   lastTime = Time[0];

   // Build candles list (recent WindowBars bars)
   int bars = MathMin(WindowBars, Bars-1);
   if(bars < 20) return; // not enough data

   // Build JSON manually
   string json = "{\"type\":\"predict\",\"candles\":[";
   for(int i=bars-1;i>=0;i--)
   {
       string item = StringFormat("{\"datetime\":\"%s\",\"open\":%.5f,\"high\":%.5f,\"low\":%.5f,\"close\":%.5f,\"volume\":%d}",
           TimeToString(Time[i], TIME_DATE|TIME_SECONDS), Open[i], High[i], Low[i], Close[i], Volume[i]);
       json += item;
       if(i>0) json += ",";
   }
   json += "]}";

   // Send JSON to Python server over ZMQ and wait for reply
   // This uses pseudocode because the exact API depends on the wrapper installed.
   // Example pseudocode:
   // string reply = ZmqSendRequest(json, 2000);
   // if(reply=="") { Print("No reply from model server"); return; }

   // For the template, we'll simulate a HOLD reply to avoid accidental trades
   string reply = "{\"action\":\"HOLD\", \"confidence\":0.5, \"stop_pips\":30, \"tp_pips\":60}";

   // Parse reply - simple parsing (improve in production)
   string action = ParseJsonField(reply, "action");
   double conf = StrToDouble(ParseJsonField(reply, "confidence"));
   int stop_pips = (int)StrToDouble(ParseJsonField(reply, "stop_pips"));
   int tp_pips = (int)StrToDouble(ParseJsonField(reply, "tp_pips"));

   if(action=="BUY" || action=="SELL")
   {
       // Check spread and other safety checks
       double spread = (Ask - Bid) / Point;
       if(spread > 50) { Print("Spread too high, skipping"); return; }

       // calculate lot size based on RiskPercent (simplified)
       double risk = AccountBalance() * RiskPercent/100.0;
       double sl_points = stop_pips;
       double lot = NormalizeDouble(risk / (sl_points * 10), 2); // very rough
       if(lot < MarketInfo(Symbol(), MODE_MINLOT)) lot = MarketInfo(Symbol(), MODE_MINLOT);

       int ticket = 0;
       if(action=="BUY")
           ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, 3, Ask - sl_points*Point, Ask + tp_pips*Point, "AIBridge", 0, 0, clrBlue);
       else
           ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, 3, Bid + sl_points*Point, Bid - tp_pips*Point, "AIBridge", 0, 0, clrRed);

       if(ticket>0)
           Print("Order sent: ", action, " ticket=", ticket);
       else
           Print("OrderSend failed: ", GetLastError());
   }
}

string ParseJsonField(string json, string field)
{
   // very small helper: find "field": and extract next token (string or number)
   int p = StringFind(json, '"' + field + '"');
   if(p==-1) return "";
   int colon = StringFind(json, ":", p);
   if(colon==-1) return "";
   int start = colon+1;
   // skip spaces
   while(start < StringLen(json) && StringGetCharacter(json, start)==32) start++;
   if(StringGetCharacter(json, start)==34) // string
   {
       start++; int end = StringFind(json, '"', start);
       return StringSubstr(json, start, end-start);
   }
   else
   {
       int end = start;
       while(end < StringLen(json) && StringGetCharacter(json,end) != ',' && StringGetCharacter(json,end) != '}' ) end++;
       return StringSubstr(json, start, end-start);
   }
}

//+------------------------------------------------------------------+
