// Adapted from google-labs-code/stitch-skills at 0337446.
// Place in video/src; copy screens.json to video/screens.json and the slide template to src/ScreenSlide.tsx.
import type {FC} from 'react';
import {Composition} from 'remotion';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {linearTiming, TransitionSeries} from '@remotion/transitions';
import {ScreenSlide} from './ScreenSlide';
import screensManifest from '../screens.json';

const transitionFrames = 20;
const {fps, width, height} = screensManifest.videoConfig;
const durations = screensManifest.screens.map((screen) => Math.round(screen.duration * fps));
if (!Number.isFinite(fps) || fps <= 0 || !durations.length || durations.some((frames) => !Number.isFinite(frames) || frames <= transitionFrames)) {
  throw new Error('Provide screens with positive fps and durations longer than the 20-frame transition.');
}
export const durationInFrames = durations.reduce((sum, frames) => sum + frames, 0)
  - (durations.length - 1) * transitionFrames;

export const WalkthroughComposition: FC = () => (
  <TransitionSeries>
    {screensManifest.screens.flatMap((screen, index) => {
      const sequence = (
        <TransitionSeries.Sequence key={screen.id} durationInFrames={durations[index]}>
          <ScreenSlide imageSrc={screen.imagePath} title={screen.title}
            description={screen.description} width={screen.width} height={screen.height} />
        </TransitionSeries.Sequence>
      );
      if (index === screensManifest.screens.length - 1) return [sequence];
      return [sequence, (
        <TransitionSeries.Transition key={screen.id + '-transition'}
          presentation={screen.transitionType === 'slide' ? slide() : fade()}
          timing={linearTiming({durationInFrames: transitionFrames})} />
      )];
    })}
  </TransitionSeries>
);

export const RemotionRoot: FC = () => (
  <Composition id="WalkthroughComposition" component={WalkthroughComposition}
    durationInFrames={durationInFrames} fps={fps} width={width} height={height} />
);
