# sdm_demo_java_jdbc_swing_thesaurus_sqlite3

Quick Demo of how to use [SQL DAL Maker](https://github.com/panedrone/sqldalmaker) + Java/JDBC/Swing.

![sdm_swing.png](sdm_swing.png)

sdm.xml

```xml

<sdm>

    <dto-class name="Word" ref="WORDS"/>

    <dto-class name="RelatedWord" ref="getRelatedWords.sql"/>

    <dao-class name="ThesaurusDao">

        <query method="getTotalWordsCount" ref="getTotalWordsCount.sql" return-type="Integer"/>

        <query-dto-list method="getWordsByKey(key)" ref="getWordsByKey.sql" dto="Word"/>

        <query-dto-list method="getRelatedWords(Integer w_id)" dto="RelatedWord"/>

    </dao-class>

</sdm>
```

Generated code in action:

```java
package com.sdm.thesaurus;

import java.util.List;

import com.sqldalmaker.DataStoreManager;
import com.sdm.com.sdm.thesaurus.dao.ThesaurusDao;
import com.sdm.com.sdm.thesaurus.dto.RelatedWord;
import com.sdm.com.sdm.thesaurus.dto.Word;

public class DataController {

    static DataStoreManager dm = new DataStoreManager();
    static ThesaurusDao dao = dm.createThesaurusDao();

    static void db_open() throws Exception {
        dm.open();
    }

    static void db_close() throws Exception {
        dm.close();
    }

    static List<RelatedWord> getRelatedWords(Word word) throws Exception {
        return dao.getRelatedWords(word.getWId());
    }

    static Integer getTotalWordsCount() throws Exception {
        return dao.getTotalWordsCount();
    }

    public static List<Word> getWordsByKey(String key) throws Exception {
        String key1 = key + "%";
        return dao.getWordsByKey(key1);
    }
}
```