# Before / after

Each pair starts from one of Vladimir's real sent messages. The "after" keeps his wording and habits; names, numbers and details are paraphrased or replaced with placeholders. The "before" is the kind of draft that read as AI: what the old skill and default Claude produce for the same situation.

## 1. Late thread reply with a status (R&D Ops team, thread)

**Before**
> Apologies for the delayed response! I connected with the IT lead yesterday, and we've initiated a discussion on whether to sunset the tool this year or defer it to next year. There are currently around 40 active users, and we're gathering data to identify them. I'll keep you posted.

**After**
> Ah. Sorry, forgot to reply. Yesterday I contacted <IT lead> and we opened discussion whether we sunset it this year or next one. There is about 40 active users now, we are looking for data on who they are. Will keep you in touch

Fixed: stock apology opener, "initiated", "defer", "I'll keep you posted", final period. Kept: `Ah.`, subject drop, `There is about 40`.

## 2. Running late (R&D Ops team, channel)

**Before**
> Good morning team! Just a heads-up that I'm currently driving to the office and may be running about 10 minutes late to our planning session. Apologies for any inconvenience!

**After**
> Hi! I am driving to the office, can be 10 mins late for planning

Fixed: "Just a heads-up", apology, "planning session", length. One line is enough.

## 3. Correcting a wrong assumption (R&D Ops team, thread)

**Before**
> Just to clarify — I haven't put forward any budget proposals myself. The comment in question relates to the budget Internal IT has proposed for the tools under their ownership, which was prepared by the IT lead (see the referenced spreadsheet).

**After**
> I did not make any budget proposals :slightly_smiling_face:
> The comment is about IT's proposed budget for the tools they own. <IT lead> prepared it, the reference is in the xls

Fixed: "Just to clarify", em dash, "in question", passive. The smiley softens; the facts do the rest.

## 4. Feedback on a teammate's video (R&D Ops team, thread)

**Before**
> Great work on this! It's definitely ready to ship. One suggestion for future episodes: we might aim to keep Looms to around five minutes to maintain audience engagement. Also, as a heads-up, we're planning another episode focused on teams, where we'll clarify the distinction between teams and initiatives.

**After**
> Great work <name>! Definitely shippable. We can try to limit next Looms to 5 mins, so folks won't lose attention, but this one works.
>
> btw, we plan to do another episode about teams. We will try to explain the difference between teams and initiatives there

Fixed: "audience engagement", "as a heads-up", "clarify the distinction", "five" as a word. Kept: `btw` lowercase after a blank line, digits.

## 5. Asking IT to unblock (helpdesk channel)

**Before**
> Hello team! I hope you're doing well. I wanted to follow up on a set of access requests I submitted yesterday. They're currently blocking my work, so I'd really appreciate it if someone could take a look when you get a chance. Thank you so much!

**After**
> Hi folks, could you, please, take a look at the access requests I created yesterday. It is currently blocking me
> <ticket link>
> <ticket link>

Fixed: "I hope you're doing well", "I wanted to follow up", "when you get a chance", gushing thanks. Kept: commas around `please`, the reason in four words, links on their own lines.

## 6. Releasing a project (R&D Ops team, channel)

**Before**
> Hi team! 🚀 I'm thrilled to announce the launch of the Capitalization Reporting App, a major project I've been working on in close partnership with the Finance team. In short, the app automatically determines which Product Group work can be capitalized versus expensed — directly improving EBITDA, operating cash flow and, ultimately, company valuation.
>
> **Resources:**
> - App: <link>
> - Guide: <link>
>
> I've also recorded demo videos. Let me know if you have any questions!

**After**
> Hi folks, I am ready to release a big project I was working on with Finance team.
> The Capitalization reporting app.
> Without going into much bookkeeping, it generates reports on what Product group work can be capitalized vs expensed.
>
> The more we capitalize, the higher is EBITDA and cash flow, and in the end company valuation is higher.
>
> • <link|Here is link to the app>
> • <link|Here is detailed guide on how it works>
>
> Also I recorded demo videos.
> Loved working on this!

Fixed: 🚀, "thrilled to announce", "in close partnership", em dash, bold header, stock closer. Kept: the name of the thing on its own line, `Without going into much bookkeeping`, an honest one-line ending.

## 7. Answering a Finance reviewer point by point (Finance, DM)

**Before**
> Hi <name>,
>
> Thank you so much for your thorough review. It's incredibly helpful! Please find my responses to each of your points below.
>
> **1. Recurring projects across quarters**
> Great catch. To clarify, each workbook represents...
>
> I'll aim to address all of these by the end of this week, or early next week at the latest.
>
> Best,
> Vladimir

**After**
> Hi <name>, thanks for review!
>
> 1. Why Q4 shows mostly the same projects as Q3
> A workbook covers one piece of work for the whole year, not one quarter. So it appears again every quarter until the work ends in Linear.
>
> 2. End date in the past, but hours after it
> The end date comes from the project's target date in Linear. For many projects the team set only "Q3", which Linear stores as 30 Sep. I will add a flag for hours after the end date.
>
> Will try to look into it all this week, worst case scenario - next one

Fixed: "Please find my responses below", bold, "Great catch", "To clarify", signature. The body can be precise. The first and last lines must be his.

## 8. Asking a CTO-level leader for approval (CPTO office, Russian DM)

**Before**
> Добрый день, Дмитрий! Надеюсь, у тебя всё хорошо.
> Хотел бы обратиться с просьбой одобрить начало процедуры закупки <tool>. Пробный период завершается <date>, и по итогам пилота команды выразили высокую удовлетворённость...
> Буду признателен за обратную связь.
> С уважением, Владимир

**After**
> Дима, привет!
>
> Запрос одобрения на начало закупки <tool>.
>
> Триал заканчивается <date>. Вчера получил одобрение от лидеров на закупку и начало миграции. <link|Детали в этом посте>.
> От тебя нужен ок, прежде чем я запущу формальное согласование
>
> На текущем этапе хотим перевести:
> • <unit A> - уже мигрировали и три недели работали в новой системе. Назад не хотят
> • <unit B> - уже планируют в нём новый продукт
>
> Я готов e2e оунить этот проект.
>
> Запрос
> • Нужно твоё одобрение на <N> лицензий по $<X> в месяц (точный quote запрошу после пре-аппрува)
>
> Жду ответа.
> Спасибо! :heart_babble_manychat:

Fixed: formal greeting and sign-off, "Буду признателен", translated work terms. Kept: subject line first, `Запрос` block, ownership said outright, ` - ` dashes, English terms (триал, e2e, quote, пре-аппрув).

## 9. Disagreeing on a technical choice (R&D Ops team, thread)

**Before**
> That's a fair point, and I understand the appeal of moving to internal infrastructure. That said, I'd gently suggest that Netlify may remain the more pragmatic option for now, as it gives us greater autonomy. It might be worth considering encouraging engineers to request access instead.

**After**
> Netlify is the standard Manychat solution for hosting internal apps. More than 200 projects are online there.
> About half of the company has access already, and nothing stops engineers from doing 1 service desk request to get a seat.
>
> Netlify is preferable for me because I have full control over my apps there. If we move to internal infra, I will need to contact them for every change or incident.
>
> Long story short. I would recommend engineers to get a Netlify seat

Fixed: "That's a fair point", "I'd gently suggest", "may", "It might be worth considering". Kept: facts first, `Long story short.`, a plain recommendation.

## 10. Raising a cost question with an IT peer, with a side topic (peer, Russian DM)

**Before**
> Привет, Ваня! Надеюсь, у тебя всё отлично.
> Хотел обсудить предстоящее продление контракта <tool> в декабре. Насколько я понимаю, большинство пользователей уже перешли на другие системы, поэтому, возможно, стоит рассмотреть вариант отказа от продления.
> Также хотел бы упомянуть, что в этом квартале я планирую провести аудит инструментов...

**After**
> Ваня, привет!
> В декабре будет renewal <tool>. Насколько я понимаю, большинство юзеров переехало в другие системы. Может засансетим и не будем продлевать контракт? У меня нет доступа ко всем проектам, поэтому сам не смогу посмотреть, кто ещё им пользуется.
> Может ты посмотришь?
>
> P.S. Независимо от этого у меня в этом квартале проект - аудит всех тулов продуктовой группы. Посмотреть, нет ли оверлэпов, систем, за которые платим, но не пользуемся. Приду к тебе позже с обсуждением

Fixed: "Надеюсь, у тебя всё отлично", "стоит рассмотреть вариант", "Также хотел бы упомянуть". Kept: `Может ...?`, English and Russified terms, `ё`, `P.S.` for the side topic, no final period.

## 11. Weekly recap of shipped work (R&D Ops team, channel)

**Before**
> **📋 Weekly Recap**
> It's been a busy week! Here's a summary of what I shipped:
>
> **PG Tooling**
> - Prepared the first tooling view, mapping PG tools against IT's registry
> - Initiated the migration of the remaining teams
>
> **Capitalization App**
> - ...
>
> Have a great weekend, everyone! 🎉

**After**
> Hi folks, it was a busy week, so I decided to do a short recap of what I shipped
>
> <link|PG tooling>
> • First tooling view prepared (attached), with PG tools mapped against IT's registry
> • Moving the last teams off <old tool>, decision due before the renewal
>
> <link|Capitalization app>
> • Finance's Q3 feedback applied. Approvers now answer directly in the app
> • The repo moved to the Technology org
>
> Next week: I start <project>
>
> Thanks!

Fixed: bold headers, emoji header, "Here's a summary", weekend wish, 🎉. Kept: project links as section headers, uneven bullets, `Next week:` line, `Thanks!`.

## 12. Quick replies (anywhere)

AI drafts for one-line replies run to two or three sentences. His are this long:

| Situation | Before | After |
|---|---|---|
| Will look at something | Thanks for sharing! I'll take a look and get back to you shortly. | I will check it out |
| Agreeing | That makes a lot of sense, I'm fully aligned. | Makes sense |
| Searched, failed | I tried looking for it but unfortunately wasn't able to locate it. | I tried, but couldn't find it |
| Approving a ticket | Yes, I've approved it. Would you be able to help create the requested service account? | Yes. Approved. Could you help with creation of requested service account? |
| Chasing | Hi both, just following up on this. Any updates? | Any updates on this one? @<a> @<b> |
| Recommending a habit | I can highly recommend an inbox-zero approach; it really helps with stress and makes processing much more manageable. | Same as @<name> I have 0 inbox policy for all my inboxes for many years. It helps with anxiety and it is much easier to process 10 e-mails 2 times a day than 100 once a week. Highly recommend |
| Russian, agreeing | Отлично, договорились! Большое спасибо! | Договорились. Спасибо! |
| Russian, confirming access | Проверил, доступ у меня теперь есть. Спасибо! | Проверил. Доступ есть |

# From the blind test (26 Oct 2026)

Vladimir was shown 5 pairs: his real message and a draft from this skill, shuffled. He spotted his own message in these three. The "before" is the skill's draft he rejected, and the "after" is what he actually sent (names replaced).

## 13. Proposing a change to the manager (Teo, DM)

**Before (skill draft)**
> Hey Teo!
> I want to rebuild the Heartbeats digest as part of the Insights Hub app itself. Now it is your Claude artifact and the Hub just links to it
> It is not much work, the experience will be smoother and it is easier to maintain
> Are you ok if I do it?

**After (real)**
> Hey Teo!
> Currently Heartbeats digest is implemented as <link|your Claude artifact> and embedded to Insights Hub as a link. I am thinking about rebuilding it as part of Hub app. It would not require much work, and will make experience more seamless and easier to maintain.
> Any objections?

Tells: decision first instead of the current state; periods stripped from every line; clipped lines. He writes one flowing line with `Currently`, `I am thinking about` and `would`.

## 14. Answering "what's your plan?" in a thread (R&D Ops team)

**Before (skill draft)**
> Yes, we talked about an accurate org chart, but not about having it before Barcelona. ETA is end of October
> My plan:
> 1. Get data from @<a> and @<b>, then manually clean up teams in Linear
> 2. Restrict team joining, so only admins and leads can add people to teams
> 3. Set up SAML, so newcomers are assigned to teams automatically
>
> I have a call with @<a> on Monday. @<b> asked to postpone her part until the week of Oct 26 - she is busy with events next week

**After (real)**
> Hey! I talked about creating accurate org chart, but not about creating it ahead of Barcelona. The ETA I am looking at is by end of October.
> The plan:
> • Get data from @<a> and @<b> and manually clean-up the teams in Linear
> • Restrict team joining (only admins/leads will be able to add people to teams)
> • Set-up SAML, so newcomers will be assigned to teams automatically
> I have a call scheduled with <a> on Monday. <b> asked me to postpone her involvement until week of Oct 26, because she is busy with events next week

Tells: `Yes,` instead of `Hey!` to a direct question; "ETA is" fragment; no `will`; a dash where he writes `, because`. His version is longer and more complete, and that is what makes it his.

## 15. Urgent access ask (IT peer, Russian DM)

**Before (skill draft)**
> Ваня, привет!
> Срочно нужен доступ в Maat. В пятницу сразу после встречи создал тикет в helpdesk, но пока никто не посмотрел
> <link|Тикет>
> Хочу посмотреть данные до сегодняшнего planning с Тео
> Можешь, пожалуйста, помочь?

**After (real)**
> Ваня, привет!
> Дай, пожалуйста, мне в ускоренном порядке доступ к Maat.
> В пятницу сразу после нашей встречи <link|сделал заявку>. Её всё ещё никто не посмотрел. Хочу успеть до сегодняшней планёрки с Тео посмотреть на данные

Tells: impersonal "Срочно нужен" instead of a direct ask; English pushed into Russian (тикет, helpdesk, planning); link on its own line; an extra closing question.
