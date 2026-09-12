I want to achieve two things: 
1. Make a budget for my expenses
2. Create a tracker to track my expenses over the month, and compare against my set budget for the month

`money_101.md` is my understanding of approaching personal finance

I need a webapp: I want a simple structure. There will be labels and groups which can be attached to every expense. Any number and combination of labels can be attached to an expense, and groups are just a collection of labels.

Dinner with visting friend can have labels of "food" (different than groceries), "friend", "friend visit nov 2026". It can then be filtered with any label then. I can see total food cost that month, total cost for expenditure with friends, how much did spend for that friend's visit to me, how much did i spend with that friend's visit on food. Etc etc. If I want I can create a group of friend's visit and food together to attach to every meal we had outside.

I want the functionality to add and edit these labels / groups. So I can add a new label on the fly for a new type of expense. 

One page to add an expense. One page that compares expense against budget, sorted by which one is exceeding. Also need the functionality to see one fund in deatil - what the expenses inside it were with timestamps, how much exceeded the budget, how much is extra from last month, etc. Also a functionality to see how can i balance exceeded budget in other budgets. Of course I would need logs of all of it so that it's traceable both in backend and in UI as the end customer without technical details. Like there must be a way to see that this expense ate into its own budget but also this other budget.

Exceeding budget should not carry over to shrinking next month's fund. But there should be a toggle for me to be able to do so. And decide if I want to shrink it across months like EMI to compensate for me not exceeding my average expenses. 

There can be pills to display budget, exceeded budget (in red), carry over budget (in darker shade of same colour ig).
The app should be minimalistic but cozy, big fonts, simple numbers. Should give options to choose from fonts, Jetbrains Mono, Fraunces, Merryweather. Very few options, but understand from the styles I have mentioned, which ones I like.

There's no need for a database, I think a csv should do? I want the data to be locally stored, and synced with backup somewhere. So that I can use it in my laptop and my phone together.
