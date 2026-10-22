# Process / Sound Alchemy

## Status

First local implementation, 22 October 2026 (Hong Kong time). This is a factual
development record, not a claim that the assignment has already been submitted.
The source was created in a new folder; the course repository was read as a style
reference. No Git repository or public submission has been created by this work.

## Starting idea

The brief calls for one meaningful input-response-feedback loop. Several ideas
were discussed with the student, including a sound mixer, a memory grid and an
image transformation tool. The student chose **Sound Alchemy** and asked the AI
assistant to handle technical implementation.

Intended user: someone curious about making a small atmosphere without knowing a
music editor. The central action is changing one of three ingredients and deciding
whether the resulting place feels right. There is no correct emotional answer.

## Scope and course connection

- Week 05: values can be made visible; here, actual mixed samples form a waveform.
- Week 06: ordered samples, sample rate, sine waves, harmonics, seeded noise,
  finite WAV output, and clear Start/Stop controls.
- Week 07: an object stores state; explicit methods change it; rendering and the
  underlying sound model are separate.

The small script structure, top-level constants, explicit parameters, `main()`
entry point and uv script metadata follow the course examples. These are new
implementations; course files were not modified or copied unchanged.

## Design and code decisions so far

1. **Three ingredients, not a complete sequencer.** Rain gives texture, bass gives
   a pulse, and bells give distinct events. Each has a level and one character
   control. This keeps the consequences of each action inspectable.
2. **Local synthesis.** The implemented version uses Python's standard library for
   synthesis and Pygame for playback/windowing. It needs no generative service,
   GPU, microphone, private recordings or external media. A fixed seed makes
   comparisons repeatable.
3. **Keep Stop reliable while updating.** A background worker makes ingredients.
   Only a result matching the current character controls is accepted; current
   volumes are applied when it arrives. A later result is not allowed
   to undo the user's Stop action. Tests exercise this interruption explicitly.
4. **Shared ingredients for listening and saving.** Playback loops the accepted
   source layers; export and the waveform combine them using the current recipe.
   The settings accompany the WAV. This avoids saving an older volume setting.
5. **A revision prompted by actual local failure.** The first UI run failed in
   Pygame's Windows system-font enumeration because a registry value was an
   integer. The implementation changed to loading existing Windows font files
   directly, with a bundled-font fallback. The next screenshot run succeeded.
6. **Project-local setup.** The Windows launcher keeps uv cache and Python inside
   the project, with no global Python command or Windows registry registration.

Local source snapshots are in ignored `.backups/` for recoverability. They are
not a substitute for the visible Git development history required by the brief.

## Usability revision / 22 October 2026

After the first implementation, the student asked about possible improvements
and approved the assistant's proposal to implement three of them:

1. **Keep volume changes continuous.** The first version generated and restarted
   the whole loop for every slider change. The revision caches three ingredients
   and changes the running Sound volumes directly. Level/master changes and
   individual layer switches preserve the phrase position. New patterns still
   restart with a short transition; making the whole mix silent stops playback.
2. **Explain the control ranges.** Quiet/Loud, Sparse/Dense, Lower/Higher and
   Fewer/More notes captions explain the consequences. Rain and bell readings
   show events per four-second loop instead of an abstract percentage.
3. **Make saved work discoverable.** A button below Save opens the export folder
   after a successful save. Missing files and folder-viewer failures receive
   recoverable messages. Exports are preserved.

The assistant identified an additional implementation issue while checking this
revision: frequent mouse moves repeatedly rebuilt the waveform. Weighted mixing
was simplified and consecutive motion events combined without dropping button
or release events. This is a local technical iteration within the approved
continuous-volume improvement.

These decisions came from a discussion and code/runtime checks, **not an observed
trial with another person**. The user-trial section below remains pending.

### Remove the duplicate Stop control

The student noticed that the separate Stop button duplicated the main button's
Play/Stop behavior and approved its removal. The interface now uses one main
button, labelled Play your mix while stopped and Stop listening while playing.
Reset moved next to it and continues to stop and restore the default recipe.
Space and Escape retain their existing behavior. This is direct student feedback,
not the separate-person trial required below.

### Rain sound revision

The student listened and reported that Rain sounded like a collection of noise,
rather than rainfall. The original generator combined a fairly constant noise
bed with short single-frequency grains. The assistant revised only this sound
ingredient: a much quieter filtered bed, varied impact/splash envelopes, brief
damped droplet tails, and lower-level distant patter. No external recording,
new dependency or model service was added. Bass and Bells synthesis and the
control meanings remain unchanged. The UI description now mentions droplets.

The new code remains seeded and bounded. Sparse and dense settings are checked
for different energy, finite headroom and zero-valued loop ends. Exported recipes
identify the revised model. The old code and sound sample are preserved; v2
rain-only and mixed samples support direct listening comparisons. Sound-design
references consulted are credited in `CREDITS.md`; their code was not copied.

This revision responded to the student's actual listening feedback. On the next
listen the student rejected v2: it sounded like hitting plastic and was less
pleasant than the original noisy version. It does not complete the required
separate-person user trial.

### Soft rain revision / v3

The assistant removed the short ringing impact model after that rejection.
Rain now has a continuous filtered-noise body, gentle irregular swells, and quiet
overlapping unpitched textures with soft starts and ends. This deliberately
changes the synthesis approach rather than retuning the rejected knock sounds.
An additional agent reviewed the DSP proposal and implementation read-only;
it did not edit files or perform a listener trial.

The initial v3 signal check measured raw RMS 0.0644, peak/RMS 4.89, and a maximum
50 ms-window RMS 1.31 times the median. These support a more even signal without
dominant impact peaks; they do not establish naturalness or pleasantness.
V3 exports carry `rain_model: soft-rain-v3`. Earlier code and audio are preserved.
The student rejected v3 as well and supplied a specific Bilibili reference for
the next revision.

### Concrete reference / v4

The student explicitly requested the Agent Reach skill to inspect
`https://www.bilibili.com/video/BV1Pe411x7JY/`. Its title is
“【Minecraft】一小时纯雨声”, by 隔壁老晨MrLchen, with a reported duration of
3,601 seconds. Agent Reach's installed `bili` backend retrieved its metadata
and audio without extracting browser cookies. No subtitle/ASR service was used.

The recording was stored only under ignored `out/reference/`. Windows' built-in
transcoder decoded 60–90 seconds for analysis. The initial custom 22.05 kHz
transcode failed; a default 48 kHz WAV profile with hardware acceleration off
succeeded. NumPy in the existing authoring runtime measured the spectrum and
strength variation. No decoder or runtime package was installed for this step.

The reference had substantially less low-frequency energy than v3. The assistant
fitted a small low/high/mid filter chain to nine measured frequency bands, then
used it on newly seeded Gaussian noise. Short overlapping strength envelopes
change density without bringing back pitched/plastic impacts. The app remains
standard-library synthesis plus Pygame; reference waveform samples are not used
at runtime. Bass, Bells and the control behavior remain unchanged.

The sum of absolute band-fraction differences fell from 0.3028 for v3 to 0.0260
for v4 over the chosen bands. The 50 ms RMS variation coefficient is 0.1069
versus 0.1143 in the reference. These measurements guide timbre/texture matching;
they do not establish perceptual identity or listening acceptance. The source
window, measurement results and fitted coefficients are recorded in
`docs/rain-reference-profile.json`. V4 listening assessment remains pending.

## From mixer to sound garden / 22 October 2026

After testing, the student reported losing interest after about one minute.
The assistant proposed optional sound-matching commissions and a visual garden.
The student chose the garden as the main experience and commissions as support:
exact listening comparisons could create a high entry barrier and frustration,
whereas direct visual changes could reward a small action immediately.

The approved revision connects Rain to moss/rainfall, Bass to roots/plant motion,
and Bells to flowers/fireflies. Four landscapes give discovery goals; they can
be named, kept and restored. Three visitor invitations provide optional broad
recipes with hints, no time limit, score or failure penalty. Reset affects the
current sounds while preserving the collection. MASTER affects speaker volume,
not plant health, discoveries or wish matching.

A review found that a balanced Dawn garden could satisfy the firefly invitation
but be refused because the exclusive landscape name was different. The rules
were changed to check each wish's own broad conditions, independently of the
landscape label. This keeps the invitation consistent with its visible hint.

Collection writes preserve previous snapshots; startup checks data and can
recover an older valid collection. Name entry blocks global playback/export
shortcuts and handles blank names. The latest Rain synthesis, Bass and Bells
were not changed by this gameplay revision. Graphics use local Pygame shapes,
with no borrowed image assets or new runtime packages.

Codex wrote the implementation with separate model and drawing code reviewed
by assistant agents. Automated event tests, state tests, rendered screenshots
and a scripted demonstration validate implementation behavior. They do not
establish whether people enjoy playing for longer. The student's report is
actual direct feedback, but it is not the brief's other-person trial.

- **AI suggestion kept:** visual gardening as immediate feedback and optional
  invitations as a reason to try another combination.
- **AI suggestion changed by the student:** sound-matching commissions as the
  main activity. The student preferred low-pressure visual exploration, so exact
  auditory comparison and numerical similarity scoring were left out.

## AI tools and authorship

**Codex** was used to brainstorm, inspect local course examples, propose the
scope, write the implementation and tests, inspect the rendered interface, and
draft these documents. The student selected the idea and approved the implementation
scope. At this stage the AI assistant produced the technical code; do not imply
that the student independently authored it. The precise model is not recorded here.

- **Suggestion kept:** three sound layers with clear controls and immediate feedback;
  the student chose this idea and approved the proposed scope.
- **Suggestion changed:** the initial sound idea included possibilities such as
  rain, low tones and bells without specifying where the sounds came from. The
  implementation narrows them to deterministic local synthesis and four-second
  loops, making the work reproducible without accounts or recordings. This was an
  assistant implementation decision, not yet a student-authored critique.
- **Technical approach revised:** system-font discovery was replaced after its
  observed Windows failure. This is a debugging decision, not user-trial evidence.

**Student reflection pending:** after using the app, record one specific AI
suggestion you personally kept and one you changed or rejected, if applicable.
Record your reasons in your own words. Do not invent a rejected suggestion.

## User trial — NOT YET PERFORMED

No other person has yet tried this experience. Automated tests and an agent's
review of a screenshot do not satisfy this requirement.

Suggested trial: give another person the open app without explaining its controls.
Ask them to create and keep a garden, then see whether they voluntarily try
another combination or open a visitor invitation. Do not explain the controls first. Observe
what they attempt, where they hesitate and whether they can stop/reset. Do not
record their identity or voice.

Fill in after an actual trial:

- Date and setting: **pending**.
- What the person tried before receiving an explanation: **pending**.
- A hesitation or surprising action: **pending**.
- Did they understand the response and next action? **pending**.
- One improvement made, or a reason to keep the design: **pending**.
- What happened when the revised design was checked: **pending**.

## Verification and remaining work

See `docs/VERIFICATION.md` for executed automated checks and local playback-device
checks. Subjective listening quality and a real trial still need human feedback.

Before submission: review the code explanation, complete the real trial and
reflection, make attributable development commits with the student's approval,
publish to the student's own public repository, check signed-out access, and
submit its URL on Canvas before 1 November 2026, 23:59 Hong Kong time.

