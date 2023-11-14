// test.ts
import { runGraphInFile, startDebuggerServer, NodeDatasetProvider } from '@ironclad/rivet-node';
import { textToSpeech } from './text_to_speech.js';
import { transcribeAudioFromMic } from './speech_input.js';
import dotenv from 'dotenv';
dotenv.config();

import { EventEmitter } from 'events';
EventEmitter.defaultMaxListeners = 100;

// project file path without file ending
const project = './memGPT';
const graph = 'yebVxRtmTpuGTOzVJ-b2j';

const openAiKey = process.env.OPEN_AI_KEY;

/**
 * Loads datasets from a file with the given project name.
 * @returns A dataset provider object.
 */
async function loadDatasets() {
  try {
    const datasetProvider = await NodeDatasetProvider.fromDatasetsFile(project + '.rivet-data');
    return datasetProvider;
  } catch (err) {
    console.error('Error loading datasets:', err);
  }
}
const datasetProvider = await loadDatasets();

const debuggerServer = startDebuggerServer({
  // port: 8081
});

await runGraphInFile(project + '.rivet-project', {
  graph: graph,
  datasetProvider: datasetProvider,
  remoteDebugger: debuggerServer,
  inputs: {},
  context: {
    new_relic_api_key: process.env.NEW_RELIC_KEY,
    run_from_node: true
  },
  externalFunctions: {
    get_user_input: async function main(): Promise<{ type: string, value: string }> {
      const apiKey: string = openAiKey;
      const transcript: string = await transcribeAudioFromMic(apiKey);
      console.log(transcript);
      return {
        type: 'string',
        value: transcript
      };
    },
    text_to_speech: async (_context, response) => {
      //console.log(response);
      await textToSpeech(response, openAiKey);
      return {
        type: 'string',
        value: response
      };
    },
  },
  onUserEvent: {},
  openAiKey: openAiKey
} as any);