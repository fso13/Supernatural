# «Хозяин Леса» — исходники приключения

Один и тот же лесной хоррор под четыре системы. Общий канон — [`00-syuzhet.md`](00-syuzhet.md);
дальше выбираете файл системы и ведёте.

На сайт выложены **три редакции** — те, что совпадают с правилами проекта. Четвёртая
(Cortex/«Supernatural») переписана под GUMSHOE «Охотников» и в исходном виде не публикуется.

| Версия | Исходник | На сайте | PDF |
|---|---|---|---|
| **D&D 5e** | [hozyain-lesa-dnd5.md](hozyain-lesa-dnd5.md) | [site/adventure-hozyain.html](../site/adventure-hozyain.html) | [adventure-hozyain-dnd5.pdf](../downloads/adventure-hozyain-dnd5.pdf) |
| **GUMSHOE** | [hozyain-lesa-gumshoe.md](hozyain-lesa-gumshoe.md) | [site-gumshoe/adventure-hozyain.html](../site-gumshoe/adventure-hozyain.html) | [adventure-hozyain-gumshoe.pdf](../downloads/adventure-hozyain-gumshoe.pdf) |
| **GUMSHOE: две серии** | [hozyain-lesa-dve-serii-gumshoe.md](hozyain-lesa-dve-serii-gumshoe.md) | [site-gumshoe/adventure-hozyain-dve-serii.html](../site-gumshoe/adventure-hozyain-dve-serii.html) | [adventure-hozyain-dve-serii.pdf](../downloads/adventure-hozyain-dve-serii.pdf) |
| **The Edge!** | [hozyain-lesa-edge.md](hozyain-lesa-edge.md) | [site-edge/adventure-hozyain.html](../site-edge/adventure-hozyain.html) | [adventure-hozyain-edge.pdf](../downloads/adventure-hozyain-edge.pdf) |

## Что где лежит

- [`00-syuzhet.md`](00-syuzhet.md) — правда, места, сцены, улики, финал и последствия.
  **Читать первым:** числа живут только в файлах систем.
- [`hozyain-lesa-dnd5.md`](hozyain-lesa-dnd5.md) — статблоки, DC, тактика, сокровища, шкалирование.
- [`hozyain-lesa-gumshoe.md`](hozyain-lesa-gumshoe.md) — цепочка улик, пулы, Стабильность,
  правило твари, карточки в формате бестиария «Охотников».
- [`hozyain-lesa-edge.md`](hozyain-lesa-edge.md) — ЧЦ, раны, стресс, светлый и тёмный кубик.
- [`hozyain-lesa-dve-serii-gumshoe.md`](hozyain-lesa-dve-serii-gumshoe.md) — то же дело
  в двух сессиях с клиффхэнгером между ними.
- `hozyain-lesa-dve-serii.md`, `hozyain-lesa-supernatural.md` — исходники в Cortex,
  из которых сделана версия «две серии» для «Охотников». Оставлены как источник.

## Что общего у всех версий

- **Правда одна:** Крон, Ильга, нож-якорь, тень ножа в груди голема, сад живых тел,
  три способа забрать нож, две фазы босса.
- **Сцены одни:** тело на тропе → следы и шёпот → поляна и стража → часовня → финал.
- **Выбор один:** убить или освободить. Награда за освобождение — не «плюшка»,
  а другая концовка.

## Сборка

```bash
python3 scripts/make_hozyain_pages.py   # страницы трёх редакций
bash scripts/make_pdfs.sh               # PDF, включая четыре «Хозяина Леса»
```

Картинки берутся из бестиария проекта (`../site/img/`): своей папки арта у приключения нет.

*Если правите канон — правьте [`00-syuzhet.md`](00-syuzhet.md), а не четыре файла.
Числа живут только в файлах систем.*
