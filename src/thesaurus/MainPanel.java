package thesaurus;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.FlowLayout;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.io.File;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;

import javax.swing.AbstractListModel;
import javax.swing.DefaultListCellRenderer;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTable;
import javax.swing.JTextField;
import javax.swing.ListModel;
import javax.swing.ListSelectionModel;
import javax.swing.SwingUtilities;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;
import javax.swing.filechooser.FileFilter;
import javax.swing.table.AbstractTableModel;
import javax.swing.table.TableColumn;

import com.sqldalmaker.thesaurus.dto.RelatedWord;
import com.sqldalmaker.thesaurus.dto.Word;

public class MainPanel extends JPanel {

	/**
	 * 
	 */
	private static final long serialVersionUID = 8189942373278143473L;
	private JTextField textField_SearchKey;
	private JLabel lblWordsCount;
	@SuppressWarnings("rawtypes")
	private JList list_Words;

	private JTextField textField;

	private Timer timer = new Timer();
	private TimerTask task = null;

	private MyTableModel tableModel;

	private List<RelatedWord> synonims;
	private JTable table;

	private class MyTableModel extends AbstractTableModel {

		private static final long serialVersionUID = 1L;

		public void refresh() {
			// http://stackoverflow.com/questions/3179136/jtable-how-to-refresh-table-model-after-insert-delete-or-update-the-data
			super.fireTableDataChanged();
		}

		@Override
		public String getColumnName(int col) {
			switch (col) {
			case 0:
				return "Part of speech";
			case 1:
				return "Word";
			}
			return "Note";
		}

		@Override
		public int getColumnCount() {
			return 3;
		}

		@Override
		public int getRowCount() {
			if (synonims == null) {
				return 0;
			}
			return synonims.size();
		}

		@Override
		public Object getValueAt(int rowIndex, int columnIndex) {

			if (synonims == null) {
				return null;
			}
			switch (columnIndex) {
			case 0:
				return synonims.get(rowIndex).getRgPartOfSpeech();
			case 1:
				return synonims.get(rowIndex).getRgwWord();
			}
			return synonims.get(rowIndex).getRgwNote();
		}

		@Override
		public void setValueAt(Object aValue, int rowIndex, int columnIndex) {
			// list.get(rowIndex)[columnIndex] = (String) aValue;
		}
	}

	/**
	 * Create the panel.
	 */
	@SuppressWarnings("rawtypes")
	public MainPanel() {
		setLayout(new BorderLayout(0, 0));

		JPanel panel = new JPanel();
		add(panel, BorderLayout.SOUTH);
		panel.setLayout(new FlowLayout(FlowLayout.CENTER, 20, 5));

		lblWordsCount = new JLabel("Words count, total: 0");
		panel.add(lblWordsCount);

		JSplitPane splitPane = new JSplitPane();
		add(splitPane, BorderLayout.CENTER);

		JPanel panel_1 = new JPanel();
		splitPane.setLeftComponent(panel_1);
		panel_1.setLayout(new BorderLayout(0, 0));

		textField_SearchKey = new JTextField();
		panel_1.add(textField_SearchKey, BorderLayout.NORTH);
		textField_SearchKey.setColumns(30);

		JScrollPane scrollPane = new JScrollPane();
		panel_1.add(scrollPane, BorderLayout.CENTER);

		list_Words = new JList();
		list_Words.addMouseListener(new MouseAdapter() {
			@Override
			public void mouseClicked(MouseEvent e) {

				// http://www.rgagnon.com/javadetails/java-0219.html
				if (e.getClickCount() == 2) {
					int index = list_Words.locationToIndex(e.getPoint());
					if (index < 0) {
						return;
					}
					ListModel dlm = list_Words.getModel();
					if (index > dlm.getSize() - 1) {
						index = dlm.getSize() - 1;
					}
					Word word = (Word) dlm.getElementAt(index);
					list_Words.ensureIndexIsVisible(index);
					reloadSynonimsTable(word);
				}
			}
		});
		list_Words.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
		scrollPane.setViewportView(list_Words);

		JPanel panel_2 = new JPanel();
		splitPane.setRightComponent(panel_2);
		panel_2.setLayout(new BorderLayout(0, 0));

		textField = new JTextField();
		textField.setEditable(false);
		textField.setColumns(10);
		panel_2.add(textField, BorderLayout.NORTH);
		
		JScrollPane scrollPane_1 = new JScrollPane();
		panel_2.add(scrollPane_1, BorderLayout.CENTER);
		
		table = new JTable();
		scrollPane_1.setViewportView(table);

		textField_SearchKey.getDocument().addDocumentListener(
				new DocumentListener() {
					private void updateFilter() {
						setFilter();
					}

					public void changedUpdate(DocumentEvent e) {
						updateFilter();
					}

					public void removeUpdate(DocumentEvent e) {
						updateFilter();
					}

					public void insertUpdate(DocumentEvent e) {
						updateFilter();
					}
				});

		tableModel = new MyTableModel();
		table.setModel(tableModel);
        {
        	TableColumn col = new TableColumn();
            col.setPreferredWidth(80);
        }
        {
        	TableColumn col = new TableColumn();
            col.setPreferredWidth(140);
        }
        {
        	TableColumn col = new TableColumn();
            col.setPreferredWidth(80);
        }
	}

    private void reloadSynonimsTable(Word word) {

        try {

        	synonims = DataController.getRelatedWords(word);
        	
        } catch (Throwable tr) {
        	
        	InternalHelpers.showError(this, tr);
        	
        } finally {

            tableModel.refresh(); // table.updateUI();
        }
    }
	
	protected void setFilter() {

		final Runnable doUpdate = new Runnable() {

			@SuppressWarnings({ "unchecked", "rawtypes" })
			public void run() {

				try {

					final List<Word> list = DataController
							.getWordsByKey(textField_SearchKey.getText());

					DefaultListCellRenderer cellRenderer = new DefaultListCellRenderer() {

						/**
						 * 
						 */
						private static final long serialVersionUID = 1L;

						@Override
						public Component getListCellRendererComponent(
								JList list, Object value, int index,
								boolean isSelected, boolean cellHasFocus) {

							Word w = (Word) value;

							return super.getListCellRendererComponent(list,
									w.getWWord(), index, isSelected,
									cellHasFocus);
						}
					};

					list_Words.setCellRenderer(cellRenderer);

					AbstractListModel listModel = new AbstractListModel() {

						/**
					 * 
					 */
						private static final long serialVersionUID = 1L;

						@Override
						public Object getElementAt(int index) {
							return list.get(index);
						}

						@Override
						public int getSize() {
							return list.size();
						}

					};

					list_Words.setModel(listModel);

				} catch (Exception e) {
					e.printStackTrace();
					InternalHelpers.showError(MainPanel.this, e);
				}
			}
		};

		if (task != null) {
			task.cancel();
		}

		task = new TimerTask() {

			@Override
			public void run() {
				// http://stackoverflow.com/questions/7411497/how-to-bind-a-jlist-to-a-bean-class-property
				SwingUtilities.invokeLater(doUpdate);
			}
		};

		timer.schedule(task, 500);
	}

	// http://www.java2s.com/Code/JavaAPI/javax.swing/JFileChoosersetFileFilterFileFilterfilter.htm
	class ExtensionFileFilter extends FileFilter {
		String description;

		String extensions[];

		public ExtensionFileFilter(String description, String extension) {
			this(description, new String[] { extension });
		}

		public ExtensionFileFilter(String description, String extensions[]) {
			if (description == null) {
				this.description = extensions[0];
			} else {
				this.description = description;
			}
			this.extensions = (String[]) extensions.clone();
			toLower(this.extensions);
		}

		private void toLower(String array[]) {
			for (int i = 0, n = array.length; i < n; i++) {
				array[i] = array[i].toLowerCase();
			}
		}

		public String getDescription() {
			return description;
		}

		public boolean accept(File file) {
			if (file.isDirectory()) {
				return true;
			} else {
				String path = file.getAbsolutePath().toLowerCase();
				for (int i = 0, n = extensions.length; i < n; i++) {
					String extension = extensions[i];
					if ((path.endsWith(extension) && (path.charAt(path.length()
							- extension.length() - 1)) == '.')) {
						return true;
					}
				}
			}
			return false;
		}
	}

	public void updateWordsCount() throws Exception {
		lblWordsCount.setText(Long.toString(DataController.getTotalWordsCount()) + " items");
	}
}
