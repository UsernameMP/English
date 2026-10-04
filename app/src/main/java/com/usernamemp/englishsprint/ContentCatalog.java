package com.usernamemp.englishsprint;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Public metadata only. Paid task payloads must eventually come from ContentDeliverySource. */
public final class ContentCatalog {
    public static final class Course {
        public final String packId, subject, competition, season;
        public final int gradeMin, gradeMax;
        Course(JSONObject o) {
            packId=o.optString("id"); subject=o.optString("subject");
            competition=o.optString("competition"); season=o.optString("season");
            gradeMin=o.optInt("grade_min",1); gradeMax=o.optInt("grade_max",12);
        }
    }
    private final List<Course> courses=new ArrayList<>();
    public ContentCatalog(Context context) {
        try {
            JSONObject root=new JSONObject(read(context,"content/catalog.json"));
            JSONArray a=root.getJSONArray("packs");
            for(int i=0;i<a.length();i++) if(a.getJSONObject(i).optBoolean("enabled",true)) courses.add(new Course(a.getJSONObject(i)));
        } catch(Exception e){ throw new IllegalStateException("Content metadata failed to load",e); }
    }
    public List<Course> courses(){ return Collections.unmodifiableList(courses); }
    public List<String> subjects(){
        List<String> out=new ArrayList<>();
        for(Course c:courses) if(!out.contains(c.subject)) out.add(c.subject);
        return out;
    }
    public List<Integer> grades(String subject){
        List<Integer> out=new ArrayList<>();
        for(Course c:courses) if(c.subject.equals(subject)) for(int g=c.gradeMin;g<=c.gradeMax;g++) if(!out.contains(g)) out.add(g);
        Collections.sort(out); return out;
    }
    public List<Course> applicable(String subject,int grade){
        List<Course> out=new ArrayList<>();
        for(Course c:courses) if(c.subject.equals(subject)&&grade>=c.gradeMin&&grade<=c.gradeMax) out.add(c);
        return out;
    }
    private static String read(Context c,String p)throws Exception{
        try(InputStream in=c.getAssets().open(p);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString(StandardCharsets.UTF_8.name());
        }
    }
}
