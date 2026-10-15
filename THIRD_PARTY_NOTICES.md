# Third-party notices

The repository's [root license](LICENSE.md) is unchanged: original material is CC BY-NC-SA 4.0; commercial use requires separate prior written permission. Third-party components are not relicensed by it.

- `scripts/vendor/clean_talking_video/transcribe.py` is copied without modification from [PoetCoderJun/clean-talking-video](https://github.com/PoetCoderJun/clean-talking-video/blob/598c95ddd72622af560188f7d9180e8fd3ed1ee0/clean-talking-video/scripts/transcribe.py), commit `598c95d`. Its [MIT license](scripts/vendor/clean_talking_video/LICENSE) is preserved alongside it.
- `scripts/vendor/clean_talking_video/build_edit_plan.py` is copied from the same MIT commit `598c95d`; `timeline.py` contains the pure timeline/subtitle helpers derived from its `render_edit.py`. The adjacent MIT notice applies to these files as well. New workflow, word-accounting, sample-splice and human-approval layers are maintained in this repository. No unrelated private product code is included.
- Hyperframes is pinned to 0.8.30. The installed package metadata identifies its license as Apache-2.0; consult that distribution's notices and upstream terms.
- GSAP is pinned to 3.14.2. Its package metadata identifies the Standard “no charge” license, linked to [GSAP's standard license](https://gsap.com/standard-license/). Do not describe this dependency as MIT or assume it changes DraftCut's non-commercial restriction.
- FFmpeg, Chrome, fonts, optional components, music and media remain subject to their own licenses. They are not bundled or granted public redistribution rights by this notice. Review rights before reusing any optional assets.
