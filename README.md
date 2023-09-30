# sdm_demo_java_jdbc_swing_thesaurus_sqlite3

Quick Demo of how to use [SQL DAL Maker](https://github.com/panedrone/sqldalmaker) + Java/JDBC/Swing.

![sdm_swing.png](sdm_swing.png)

dto.xml

```xml

<dto-classes>

    <dto-class name="Word" ref="WORDS"/>

    <dto-class name="RelatedWord" ref="thesaurus/getRelatedWords.sql"/>

</dto-classes>
```

dao.ThesaurusDao.xml

```xml

<dao-class>


</dao-class>
```

Generated DAO class:

```java
package thesaurus;

import java.util.List;

import com.sqldalmaker.DataStoreManager;
import com.sqldalmaker.thesaurus.dao.ThesaurusDao;
import com.sqldalmaker.thesaurus.dto.RelatedWord;
import com.sqldalmaker.thesaurus.dto.Word;

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