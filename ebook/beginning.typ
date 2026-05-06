//-----------------------------------------------------------------------------
// Title page
#align(
  center + horizon,
  {
    set text(size: 15pt)
    [
      Vulkan Tutorial

      Alexander Overvoorde

      May 2026
    ]
  }
)

// Start page numbering
// #counter(page).update(1)
#set page(
  numbering: (..nums) => {
    text(
      font: "Liberation Serif",
      strong(str(nums.pos().first()))
    )
  },
)

//-----------------------------------------------------------------------------
// Table of contents
#show outline.entry.where(level: 1): it => {
  set block(above: 2em)
  let inner = {
    it.body()
    // `repeat[ ]` means fill with spaces. Could use `repeat[.]` to fill with dots
    box(width: 1fr, repeat[ ])
    it.page()
  }
  strong(it.indented(it.prefix(), inner))
}

#outline(indent: 2em)

//-----------------------------------------------------------------------------
