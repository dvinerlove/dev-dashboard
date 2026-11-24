# Apple Human Interface Guidelines — Dark Mode

- URL: https://developer.apple.com/design/human-interface-guidelines/dark-mode
- Publisher: Apple (official HIG — the desktop-native authority for a PyQt macOS/Windows app)
- Tier: L1
- Source class: official-docs
- Fetched: 2026-11-23 (full page)

## Key verbatim quotes

- "the system uses a dark color palette for all screens, views, menus, and controls, and may also use greater perceptual contrast to make foreground content stand out against the darker backgrounds."
- "The color palette in Dark Mode includes dimmer background colors and brighter foreground colors. It's important to realize that these colors aren't necessarily inversions of their light counterparts."
- Contrast floor: "make sure the contrast ratio between colors is no lower than 4.5:1. For custom foreground and background colors, strive for a contrast ratio of 7:1, especially in small text."
- Base/elevated model: "the system uses two sets of background colors — called base and elevated — to enhance the perception of depth when one dark interface is layered above another. The base colors are dimmer, making background interfaces appear to recede, and the elevated colors are brighter, making foreground interfaces appear to advance."
- Semantic colors: "Semantic colors (like labelColor and controlColor in macOS) automatically adapt to the current appearance... Avoid using hard-coded color values."
- Images/icons on dark: "Soften the color of white backgrounds"; dark icons may need "a slight border to make the edge visible against a dark background."
- Text: "Use the system-provided label colors for labels. The primary, secondary, tertiary, and quaternary label colors adapt automatically" — a 4-level text hierarchy.
- When dark-only is OK: "it can make sense for an app that supports immersive media viewing to use a permanently dark appearance."
