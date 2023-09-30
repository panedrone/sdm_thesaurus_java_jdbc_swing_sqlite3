package thesaurus;

import java.awt.Component;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

import javax.swing.JOptionPane;

public class InternalHelpers {

	static String getConfigFileName(String relPath) {
		return "sqldalmaker/" + relPath;
	}

	public static void showError(Component c, Throwable e) {

		JOptionPane.showMessageDialog(c,
				e.getClass().getName() + ":\n" + e.getMessage());

	}

	// http://www.devdaily.com/blog/post/java/read-text-file-from-jar-file
	public static String readFromJARFile(String resName) throws Exception {

		InputStream is = getResourceAsStream(resName);

		try {

			InputStreamReader reader = new InputStreamReader(is);

			try {

				return loadText(reader);

			} finally {

				reader.close();
			}

		} finally {

			is.close();
		}
	}

	private static InputStream getResourceAsStream(String resName)
			throws Exception {

		// swing app wants 'resources/' but plug-in wans '/resources/' WHY?

		ClassLoader cl = InternalHelpers.class.getClassLoader();

		InputStream is = cl.getResourceAsStream(resName);

		if (is == null) {
			is = cl.getResourceAsStream("/" + resName);
		}

		if (is == null) {
			throw new Exception("Resource not found: " + resName);
		}

		return is;
	}

	public static String loadText(InputStreamReader reader) throws IOException {

		int len;
		char[] chr = new char[4096];
		final StringBuffer buffer = new StringBuffer();

		while ((len = reader.read(chr)) > 0) {
			buffer.append(chr, 0, len);
		}

		return buffer.toString();

	}
}
