package com.usernamemp.englishsprint;

/**
 * Band-limited 16 kHz -> 8 kHz PCM conversion for the fixed T-One frontend.
 * No VAD, normalization, speech editing or dropped disfluencies.
 * Pure Java to keep offline conversion independently testable.
 */
public final class Pcm16To8kResampler {
    private Pcm16To8kResampler() {}
    private static final int TAPS = 63;
    private static final double[] LOWPASS = lowpass();

    private static double[] lowpass() {
        double[] kernel = new double[TAPS];
        final double cutoff = 0.22; // cycles per 16kHz input sample; Nyquist at 0.25
        double sum = 0;
        for (int j = 0; j < TAPS; j++) {
            int n = j - (TAPS - 1) / 2;
            double ideal = n == 0 ? 2 * cutoff :
                    Math.sin(2 * Math.PI * cutoff * n) / (Math.PI * n);
            double window = 0.54 - 0.46 * Math.cos(2 * Math.PI * j / (TAPS - 1));
            kernel[j] = ideal * window;
            sum += kernel[j];
        }
        for (int j = 0; j < TAPS; j++) kernel[j] /= sum;
        return kernel;
    }

    /** Byte input is little-endian mono signed PCM16 at exactly 16000 Hz. */
    public static float[] convert(byte[] pcm) {
        if (pcm == null || pcm.length == 0 || (pcm.length & 1) != 0)
            throw new IllegalArgumentException("Missing or misaligned 16 kHz PCM16");
        final int sampleCount = pcm.length / 2;
        final float[] result = new float[(sampleCount + 1) / 2];
        for (int i = 0; i < result.length; i++) {
            int center = 2 * i;
            double filtered = 0.0;
            for (int k = 0; k < TAPS; k++) {
                int source = center + k - (TAPS - 1) / 2;
                if (source < 0 || source >= sampleCount) continue;
                int offset = 2 * source;
                short value = (short) ((pcm[offset] & 0xff) |
                                       ((pcm[offset + 1] & 0xff) << 8));
                filtered += LOWPASS[k] * (value / 32768.0);
            }
            result[i] = (float) Math.max(-1, Math.min(1, filtered));
        }
        return result;
    }
}
