#figure(
  align(center)[#table(
    columns: 2,
    align: (auto,auto,),
    table.header([Header 1], [Header 2],),
    table.hline(),
    [Cell 1], [Cell 2],
    [Cell 3], [Cell 4],
  )]
  , kind: table
  )

#figure(
  align(center)[#table(
    columns: 3,
    align: (left,center,right,),
    table.header([Left], [Center], [Right],),
    table.hline(),
    [L], [C], [R],
  )]
  , kind: table
  )
