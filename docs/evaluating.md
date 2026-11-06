# Evaluating a skill

An eval runs an agent on a realistic prompt with and without the skill, then grades the results. Run them after a change to `SKILL.md` or a reference file, because unit tests cover the scripts and say nothing about what an agent does with the instructions.

Cases live in `evals/writing-technical-documentation/`, outside the skill, so they do not ship to users. Each run costs real tokens, so run one case while iterating and all of them before a release.

## Run with Claude Code

`claude plugin eval` (Claude Code v2.1.269 or later) expects an `evals/` folder inside the skill, so copy the cases in for the run. Git ignores the copy.

```bash
cp -R evals/writing-technical-documentation skills/writing-technical-documentation/evals
cd skills/writing-technical-documentation
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
cd ../..
rm -rf skills/writing-technical-documentation/evals
```

## Run by hand or with another agent

For each case, in a fresh session with no other context:

1. Copy `evals/writing-technical-documentation/files/orderflow/` to an empty folder, and make it a git repo with one commit, so a run can show what changed. Give the agent a copy of the skill.
2. Give the agent the skill, and the prompt from the case's `prompt.md`. For a baseline, use the previous skill version from git, or no skill.
3. Save the document it produced to `<workspace>/iteration-N/<case>/<config>/outputs/`, its closing message to `outputs/final_message.md`, and the folder it worked in to `<config>/repo/`.

Then grade:

```bash
python3 tests/grade_evals.py <workspace>/iteration-N
```

The script writes `grading.json` for each run, and prints each failed assertion with its evidence. It decides what a script can. An assertion it leaves undecided needs a person or an LLM grader to read the output and the transcript.

## Read the results

- An assertion that passes with and without the skill tests nothing the skill adds. Replace it.
- An assertion that fails in both is too hard or broken, or it shows a gap in the skill.
- An assertion that passes only with the skill shows the skill's value. Find which instruction did it, and keep that instruction prominent.
- Read the outputs too. Assertions only check what you thought to write down.
- Read the transcript when a run is slow. Wasted steps usually come from vague instructions or from ones that do not apply to the task.

When a run shows a mistake the skill should prevent, add one line to the Gotchas section of `SKILL.md`, and add an assertion so it stays fixed. Keep the fix general: a skill tuned to this fixture helps nobody.

## Optimize the description

The description decides whether the skill loads at all. Its trigger is a separate test from its output quality. Write about 20 realistic queries, half that should load the skill and half near-misses that should not, split them into train and validation sets, and run each query several times. The method is at [agentskills.io](https://agentskills.io/skill-creation/optimizing-descriptions).
