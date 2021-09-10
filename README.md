# PADKP
This bot runs alongside your EverQuest client, reads your log file, and helps you manage auctions.


## Quick start

#### Raiders
* Wait until you see a tell that looks like this: `Soandso tells the raid, '!Bids Open Cloak of Flames'`
* Send a tell to that player. Send the item link, then your bid. Follow this format: `/t Soandso Cloak of Flames 50`
* Make sure you use the *item link* in your tell. You don't technically *have* to, but doing so will ensure your spelling and spacing was right.
* If you're bidding for an alt, send item link, then your bid, then "alt" or "box", like this: `/t Soandso Cloak of Flames 50 alt`
* Whole numbers of points only, no fractions.
* If you send repeated bids for the same item, the LAST one is the one that counts.
* If you wish to bid for multiple items when there are duplicate drops just them all as one tell. `/t Soandso Cloak of Flames 15, 25 alt`
* Good luck!

#### Loot Team
* Open the PADKP executable
* Enter your API Token given to you by an admin (if you need to change this later, you can select reset token from the menus)
* Click "open log file" and give it the path to your log. (This file will be opened again automatically in the future)
* Open an auction like this: `/rsay !Bids Open itemlink || ANY COMMENTS GO HERE`. Capitalization and spacing in the command don't matter, but make sure to use the item link.
* If there's more than one, include the number of items like this: `/rsay !Bids Open itemlink !NUMBER || ANY COMMENTS GO HERE`
* If everything went well, the auction will appear in your window.
* Once bids are in, close the auction like this: `/rsay !Bids Closed itemlink || ANY COMMENTS GO HERE`
* The window should tell you who won, and put the /rsay congrats message into your copy buffer automatically. You can also rigt click on the auction and select 'copy gratz message'
* A succesful auction will be highlighted green, an auction with warnings will be orange, and a manually corrected auction will be yellow. Cancelled auctions are removed from the display.
* If you want to see the bids, select an auction from the window and click "Auction details". A window will open showing who bid and how much.
* The Auction details will also show any warnings after the auction has closed.
* See below for documentation and more examples of valid commands.
* If you have a problem, send a bug report to Quaff with a description of what you expected to happen, what actually happened, and a copy of your log. The more information the better.

## Commands
All commands recognized by the parser are prefixed with an exclamation point (`!`). If you want to include additional, human readable information along with your command, you can use a comment, which is prefixed by two "vertical bar" or "pipe" symbols, like this: `/rs !MY COMMAND || my comment`

#### Start an auction
`/rsay !BIDS OPEN itemlink`

The parser can handle variations in spacing and capitalization, so the following lines all do the exact same thing:
<pre>
* You tell your raid, 'bids open Singing Steel Breastplate'
* You tell your raid, '!BIDS OPEN Singing Steel Breastplate'
* You tell your raid, '!Bids Open Singing Steel Breastplate'
* You tell your raid, '!Bids open Singing Steel Breastplate || TELLS TO ME'
* You tell your raid, '   !Bids          open    Singing Steel Breastplate         || HELP MY SPACEBAR IS STICKING'
</pre>

You can also start an auction for multiple identical items, by putting `!N` (where `N` is the number of items), before or after the itemlink, like this:
* `You tell your raid, 'bids open !2 Cloak of Flames || Top Two Bids Win!'`
* `You tell your raid, 'bids open Cloak of Flames !4 || HOLY COW THERE ARE FOUR!'`

#### Bid on an auction
`/t Soandso itemlink #`

You bid on an auction by sending a tell to the person who opened the auction. The tell should contain the item link, followed by the value of your bid. You may also include a comment. All of these tells will bid 50DKP for a Cloak of Flames

* `You tell Soandso, 'Cloak of Flames 50'`
* `You tell Soandso, 'Cloak of Flames 50|| hope I win it'`
* `You tell Soandso, ' Cloak of Flames   50'`

If the bid is for an alt or box, you need to say so, like this

* `You tell Soandso, ' Cloak of Flames 50 alt'`
* `You tell Soandso, ' Cloak of Flames 50 box'`

If you are an recruit, inactive, or FNF please label your bid as such

* `You tell soandso, 'Cloak of Flames 50 recruit'
* `You tell soandso, 'Cloak of Flames 50 inactive'
* `You tell soandso, 'Cloak of Flames 50 fnf'

The bid will NOT register if you send it before the auction opens, so wait until you see a !BIDS OPEN message before you send a tell. The bid will NOT register if you don't follow the format: the item link, then the bid. Only whole number bids are accepted, no fractions.

If you are on a registered alt, bids will automatically be considered as alt bids, tag your bid as main to specify a bid as coming from your main.

* `You tell soandso, 'Cloak of Flames 50 main'

#### Close an auction
`/rs !BIDS CLOSED itemlink`

As always, the capitalization and spacing can vary.
* `You tell your raid, '!BIDS CLOSED Singing Steel Breastplate'`
* `You tell your raid, '!Bids Closed Singing Steel Breastplate'`
* `You tell your raid, '!Bids closed Singing Steel Breastplate || COLLUSION!?'`

Once the bot sees a close message, it submits the bids to padkp.net for resolution. The results of the auction will be put in your copy buffer and any warnings that might have occurred can be viewed in auction details. No further action is required unless there's been a mistake.
If you do not close the auction, it will expire after 30 minutes. This is to prevent unclosed auctions in your log, perhaps from previous raids, causing confusion in the future.

#### Cancel an auction
`/rs !CANCEL itemlink`

End an open auction without picking a winner. Perhaps the auction was somehow screwed up, and you want to start over. Or perhaps there was a complex situation and you want to switch to handling the item manually.


#### Override an auction result
`/rs !CORRECTION !AWARD itemlink !TO Player DKP-value`

Override the result of an auction to show it as concluded in favor of the specified player for the specified value. Examples:
* `You tell your raid, '!CORRECTION !AWARD Cloak of Flames !TO Quaff 30'`
* `You tell your raid, '!CORRECTION !AWARD Cloak of Flames !TO Quaff 30 Lyfeless's alt 35'`
* `You tell your raid, '!CORRECTION !AWARD Cloak of Flames !TO Quaff 30, Lyfeless's alt 35'`

The corrected auction will be colored yellow in the application once the correction is resolved with the server.

## The user interface
The user interface displays all of the auctions that it sees in your log, with the most recent auctions at the top of the window.

![](https://i.imgur.com/Sh4Kkqq.png)

 You can select an auction and use the "Auction details" option to see the bids for an auction.

![](https://i.imgur.com/6F07IaF.png)

Any possibly malformed bid tells that the bot doesn't recognize will be printed at the bottom of the tool

![](https://i.imgur.com/VZWFKwg.png)

Completed auctions are marked in green, Corrected Auctions in yellow

![](https://i.imgur.com/t26Wx40.png)

![](https://i.imgur.com/KnKyRmq.png)

Any warnings will highlight the auction in orange, and more information can be found in the details.

![](https://i.imgur.com/oi8i9CT.png)

# Dev Notes

`pip install -r requirements.txt`

Run Tests
`python -m pytest`

Build Release
* Change version in setup.py
`python setup.py py2exe`

Code formatted with autopep8

