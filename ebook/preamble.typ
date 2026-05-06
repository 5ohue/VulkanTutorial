//-----------------------------------------------------------------------------
// Page settings
#set page(
  paper: "a5",
  width: 145mm,
  height: 205mm,
  margin: (left: 15mm, right: 15mm, top: 16mm, bottom: 20mm),
  footer-descent: 3mm,
)

//-----------------------------------------------------------------------------
// Test font
#set text(
  font: "Liberation Serif",
  size: 10pt,
)

#show raw: set text(font: "JetBrainsMonoNL NF")
#show raw: set text(font: "FantasqueSansM Nerd Font")
// #show raw: set text(font: "Liberation Mono")

#set text(font: "New Computer Modern")

//-----------------------------------------------------------------------------
// Paragraphs
#set par(
  justify: true,
  // first-line-indent: (amount: 1.5em, all: true)
)

//-----------------------------------------------------------------------------
// Heading
#set heading(
  numbering: (..nums) => {
    // Only have a number if it's a top level section
    if nums.pos().len() == 1 {
      nums.pos().first()
    } else []
  },

  // Do not indent
  hanging-indent: 0pt,
)

// Don't justify long headers
#show heading: set par(justify: false)

// Change header fonts
// #show heading: set text(font: "Roboto")

// For each top level section
#show heading.where(level: 1): it => {
  pagebreak()           // New page before section
  {
    // Huge text size
    set text(size: 22pt)

    grid(
      columns: (auto, 1fr),
      rows: (auto),
      gutter: 0.5em,
      {
        let header_num = counter(heading).get().first()
        if header_num > 0 {
          text(
            fill: rgb("#666666"),
            size: 70pt,
            [#header_num ]
          )
        }
      },
      align(
        left + bottom,
        it.body,
      )
    )
    // align(center, it)     // Center
    v(0.667em)            // Small margin between section and text
  }
}

//-----------------------------------------------------------------------------
// Code blocks
#import "@preview/codly:1.3.0": *
#import "@preview/codly-languages:0.1.1": *
#show: codly-init.with()

#set raw(
  theme: none,
)

//-----------------------------------------------------------------------------
