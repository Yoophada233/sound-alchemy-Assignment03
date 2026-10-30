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

The following notes are based on my experience optimizing different versions during user testing.

- [Simplified Playback Controls] Users noticed that the main playback button on the page already stopped the sound, so having a separate [Stop] button next to it seemed redundant. I subsequently removed the standalone Stop button and standardized the interface to a single Play/Stop button.

- [Rain Sound Optimization] After multiple test listens, users felt the rain sounds resembled TV static; after modifications, they sounded like tapping on plastic. I subsequently provided a specific Minecraft rain sound video as a reference and readjusted the texture of the synthesized rain sounds.

- [Gameplay Loop Enhancement] Users lost interest in the original mixer after about a minute, feeling that simply adjusting the sound wasn’t engaging enough. Subsequently, I added gameplay where sounds directly affect the garden and introduced visitor quests as optional objectives to lower the learning curve.

- [Mute Status Indicator] Users reported not hearing rain sounds even when DROPS was set to maximum; upon inspection, I found that the “Rain” LEVEL was set to zero. We subsequently added prompts for the three sound effect sections and disabled the parameters below when the volume was set to zero or the app was closed to reduce confusion.

- [Feedback on Invalid Recipes] When users discovered that a recipe did not meet the requirements, clicking “Share this garden” produced no obvious reaction, leading them to assume the app had crashed. We subsequently added a mail animation and specific adjustment prompts to let users know why the task was not completed.

- [Reset on Each Session] When new users opened the app, all tasks and collectibles were already completed. We subsequently updated the app so that tasks, discoveries, and saved gardens reset upon reopening, ensuring each session starts from the beginning.

- [Collectible Unlock Feedback] Users found that unlocked collectibles weren’t prominent enough and wanted more content to explore. We subsequently added unlock notifications and collectible animations, and expanded the number of discoverable gardens to eight.

- [Background and Interface Style] Users felt that the early all-yellow background was unattractive, and later interfaces had a templated look. During adjustments, plants, mist, and a dark garden atmosphere were gradually added to make the background, controls, and collectibles better align with the theme.

- [Screen Adaptation Optimization] Users noticed that text and the overall image appeared blurry on 2K screens, and this was even more pronounced on 4K screens. The original fixed-size interface lost clarity when scaled up, so we subsequently changed the system to render text and the interface based on the actual window resolution.

- [Main Operation Guidance] Users wanted new players to discover more naturally that “tapping a flower changes the melody.” We subsequently moved the main play button into the scene and emphasized flower numbers, RING/REST statuses, and beat cues to make interactive elements more prominent.

- [Collection and Exploration] Users want the collection process to feel more exploratory, rather than simply adjusting numbers based on a percentage. Moving forward, we’ll implement layered prompts: first providing auditory cues and scene-based clues, then expanding to more specific hints as needed to encourage users to listen and experiment.

- [Scene Layering and Softening] Users want the art style to feel more immersive, while noting that the realistic elements are too grainy and overly sharpened. Future iterations will incorporate layers of distant mountains, forests, lake surfaces, and foreground vegetation, while softening the natural textures.

- [Sound Loop Transitions] Users noted noticeable stuttering and abrupt transitions at the end of each loop for the Rain and Bass sounds. Future updates will refine the filtering transitions at the beginning and end of the rain sound to better align with the bass waveform, remove the fade-in/fade-out effects at the edges of each loop, and reduce the sense of interruption during repeated playback.

- [Immersive Plant Borders] After comparing the actual interface with the previous design mockups, users expressed a desire for three-dimensional plant decorations along the page edges. We subsequently added branches, leaves, vines, and ferns with highlights and soft shadows, extending them into the white space on both sides of the widescreen layout.
