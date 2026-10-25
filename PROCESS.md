# Process

## Tools and collaboration

I used Codex to develop Sound Alchemy, referring to the assignment requirements and the Python examples from Weeks 05, 06 and 07. I chose the sound-mixing idea and asked Codex to handle the technical work. The intended user is someone who wants to make a small sound atmosphere without learning a pefessional music editor.

Codex wrote the Python code, automated tests and most of the documentation. I was responsible for choosing the direction, testing versions myself and giving feedback on the sound, visual design and controls. When something sounded wrong, looked unclear or did not respond as I expected, I described the problem and sent screenshots or a reference.

The rain, bass and bells are synthesized locally, and the garden and specimen illustrations are drawn with Pygame code. They are not downloaded recordings or AI-generated image files. I supplied a Minecraft rain video as a listening reference for the rain revision. Codex analysed a short section to guide the synthesized texture; the recording is not used as a runtime asset or included in the public project materials. The reference is credited in `CREDITS.md`.

## The things I kept

I kept the three ingredients, Rain, Bass and Bells, because their roles are easy to distinguish. Each has a volume control and one sound-character control. I also kept local synthesis and WAV export, so someone can use the experience without an account or microphone and keep a sound they have made.

After trying the original mixer, I lost interest after about one minute. I wanted more reasons to continue experimenting. Codex proposed a visual garden and sound-matching tasks, and I chose to combine them with the garden as the main activity. Adjusting a sound directly changes rain, moss, roots, flowers and lights. Visitor requests remain optional, with broad conditions and no timer or penalty, because I thought exact listening comparisons could be difficult and frustrating for beginners.

I accepted the later night-greenhouse and specimen-notebook direction. The garden became the main visual area, visitor notes moved into letters, and export controls were tucked away until needed. I kept the idea of giving each discovery its own illustration and showing all eight together. Saved gardens also gained thumbnails of their actual recipes.

I also accepted the four-flower melody. Clicking numbered flowers adds or removes bells from a four-second loop, while a firefly marks the beats. This gives users something of their own to compose and keep. Sparkle now controls how long the bells ring and the flower glow rather than overwriting the selected notes. Whether this makes the experience interesting for longer still needs to be tested with someone else.

## The things I rejected

I rejected several rain revisions after listening to them. The first sounded more like television noise than rain. A later attempt sounded like knocking on plastic, and another revision still did not give me the texture I wanted. Instead of asking for more vague adjustments, I provided a specific Bilibili reference. I still need to listen to the latest version again before deciding how well it matches the reference.

I questioned the separate Stop button because the main Play button already changed to Stop during playback. I asked for the duplicate control to be removed. The interface now has one main playback button, with Reset beside it.

I also disliked the plain yellow background and later asked how the interface could feel less like an AI-generated template. I wanted a visual style that belonged to the garden theme. The revisions introduced a mist-green background, botanical drawings and the notebook layout, while keeping the controls readable.

## Corrections and validation

When I increased DROPS to its maximum and heard nothing, my screenshots showed Rain LEVEL at zero. The same confusion could occur with the other ingredients. I asked for clearer prompts and for the lower controls to be disabled when their ingredient is muted or switched off. This made it clearer that DROPS, PITCH and SPARKLE modify a sound rather than act as independent sound sources.

I also noticed that clicking Share this garden with an unsuitable recipe seemed to do nothing. I asked for visible feedback so users would not assume the app was broken. The letter now pulses and shows a specific adjustment to try before sharing again.

Discoveries were another place where a response could be missed. I requested more noticeable unlock feedback and additional things to collect. The project now has eight discoveries, with named notices, distinct specimens and a leaf-filing animation. I also asked for discoveries, visitor stamps and kept gardens to reset on reopening, so each new visitor starts with their own unfinished experience.

My manual checks focused on what I could see and hear. Codex ran the automated checks for sound generation, controls, recipe restoration and export, with details in [the verification record](docs/VERIFICATION.md). These checks and the scripted demonstrations help explain the implementation, but they do not establish that another person understands or enjoys it.

## User trial
