package com.usernamemp.englishsprint;

public final class TOneResamplerTest {
    private static void check(boolean p, String msg) {
        if (!p) throw new AssertionError(msg);
    }

    public static void main(String[] args) {
        int n = 16000;
        byte[] pcm = new byte[n * 2];
        for (int i = 0; i < n; i++) {
            int value = (short) Math.round(20000 * Math.sin(2 * Math.PI * 900 * i / 16000));
            pcm[2*i] = (byte) value;
            pcm[2*i + 1] = (byte) (value >>> 8);
        }
        float[] out = Pcm16To8kResampler.convert(pcm);
        check(out.length == 8000, "Duration 1s 16kHz -> 8kHz");
        double power = 0;
        for (int i = 80; i < out.length - 80; i++) power += out[i] * out[i];
        check(power / (out.length - 160) > 0.10, "Pass-band 900Hz attenuated");
        // Anti-alias: 6 kHz at the original 16 kHz must not become 2 kHz.
        for (int i = 0; i < n; i++) {
            int value = (short) Math.round(20000 * Math.sin(2 * Math.PI * 6000 * i / 16000));
            pcm[2*i] = (byte) value;
            pcm[2*i + 1] = (byte) (value >>> 8);
        }
        float[] alias = Pcm16To8kResampler.convert(pcm);
        double aliasPower = 0;
        for (int i = 80; i < alias.length - 80; i++) aliasPower += alias[i] * alias[i];
        check(aliasPower / (alias.length - 160) < 0.001, "6kHz alias too strong");
        boolean bad = false;
        try { Pcm16To8kResampler.convert(new byte[1]); }
        catch (IllegalArgumentException expected) { bad = true; }
        check(bad, "Odd-length PCM must be rejected");
        System.out.println("T-One 16kHz-to-8kHz conversion: PASS");
    }
}
