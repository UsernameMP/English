package com.usernamemp.englishsprint;

import android.content.Context;

/**
 * Trust boundary for protected learning content.
 * Production implementations fetch bounded, authorized envelopes from a backend.
 * The bundled source exists only for the current pilot/demo transition.
 */
public interface ContentDeliverySource {
    final class Request {
        public final String subject, packId;
        public final int grade, limit;
        public Request(String subject,int grade,String packId,int limit){
            this.subject=subject;this.grade=grade;this.packId=packId;this.limit=Math.max(1,Math.min(limit,30));
        }
    }
    final class Envelope {
        public final String payload, version, expiresAt;
        public Envelope(String payload,String version,String expiresAt){this.payload=payload;this.version=version;this.expiresAt=expiresAt;}
    }
    Envelope fetch(Context context, Request request) throws Exception;
}
