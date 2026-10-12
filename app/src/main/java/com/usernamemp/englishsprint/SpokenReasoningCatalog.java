package com.usernamemp.englishsprint;
import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Versioned allow-list: collection eligibility does not imply validated reasoning. */
public final class SpokenReasoningCatalog {
    private static Set<String> ids;
    private SpokenReasoningCatalog() {}
    private static synchronized void load(Context context) {
        if(ids!=null)return;
        Set<String> found=new HashSet<>();
        try(InputStream in=context.getAssets().open("content/spoken_reasoning_candidates.json");
            ByteArrayOutputStream out=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[4096]; int n;
            while((n=in.read(buffer))!=-1)out.write(buffer,0,n);
            JSONArray rows=new JSONObject(out.toString("UTF-8")).getJSONArray("candidates");
            for(int i=0;i<rows.length();i++)found.add(rows.getJSONObject(i).getString("question_id"));
        } catch(Exception e) {throw new IllegalStateException("Voice candidate catalog invalid",e);}
        ids=found;
    }
    public static boolean isEligible(Context c,String questionId) {
        load(c); return ids.contains(questionId);
    }
    public static boolean hasCandidates(Context c,List<Question> available) {
        load(c);
        for(Question q:available)if(ids.contains(q.id)&&"numeric".equals(q.interaction))return true;
        return false;
    }
}
