package thesaurus;

import java.awt.BorderLayout;
import java.awt.EventQueue;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextPane;
import javax.swing.SwingConstants;
import javax.swing.JTextArea;

public class ThesaurusApp {

	private JFrame frame;
	private MainPanel mainPanel;
	private JTextPane textPane_DTO;
	private JTextArea textArea_DAO;

	/**
	 * Launch the application.
	 */
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					DataController.db_open();
					ThesaurusApp window = new ThesaurusApp();
					window.frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
					InternalHelpers.showError(null, e);
				}
			}
		});
	}

	/**
	 * Create the application.
	 */
	public ThesaurusApp() {
		initialize();
	}

	/**
	 * Initialize the contents of the frame.
	 */
	private void initialize() {
		frame = new JFrame();
		frame.setTitle(getClass().getName());
		frame.setBounds(100, 100, 1024, 768);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setLocationRelativeTo(null); // place a window in the center of
											// the screen

		JTabbedPane tabbedPane = new JTabbedPane(JTabbedPane.TOP);
		frame.getContentPane().add(tabbedPane, BorderLayout.CENTER);

		mainPanel = new MainPanel();
		tabbedPane.addTab("Thesaurus", null, mainPanel, null);

		JScrollPane scrollPane_1 = new JScrollPane();
		tabbedPane.addTab("DB-diagram", null, scrollPane_1, null);

		JLabel label = new JLabel("");
		label.setVerticalAlignment(SwingConstants.TOP);
		label.setIcon(new ImageIcon(ThesaurusApp.class
				.getResource("/thesaurus/db-diagram.png")));
		scrollPane_1.setViewportView(label);

		JScrollPane scrollPane_2 = new JScrollPane();
		tabbedPane.addTab("DTO XML", null, scrollPane_2, null);

		textPane_DTO = new JTextPane();
		scrollPane_2.setViewportView(textPane_DTO);

		JScrollPane scrollPane_3 = new JScrollPane();
		tabbedPane.addTab("DAO XML", null, scrollPane_3, null);

		textArea_DAO = new JTextArea();
		scrollPane_3.setViewportView(textArea_DAO);

		JScrollPane scrollPane = new JScrollPane();
		tabbedPane.addTab("About", null, scrollPane, null);

		final JTextPane textPane_About = new JTextPane();
		scrollPane.setViewportView(textPane_About);

		frame.addWindowListener(new WindowAdapter() {
			@Override
			public void windowOpened(WindowEvent e) {

				try {

					String dto = InternalHelpers
							.readFromJARFile(InternalHelpers
									.getConfigFileName("dto.xml"));

					textPane_DTO.setText(dto);
					textPane_DTO.setEditable(false);

					String dao = InternalHelpers
							.readFromJARFile(InternalHelpers
									.getConfigFileName("dao.ThesaurusDao.xml"));

					textArea_DAO.setText(dao);
					textArea_DAO.setEditable(false);

					String about = InternalHelpers
							.readFromJARFile("README_th_en_US_v2.txt");

					textPane_About.setText(about);
					textPane_About.setEditable(false);

					mainPanel.updateWordsCount();

				} catch (Exception e1) {
					e1.printStackTrace();
					InternalHelpers.showError(frame, e1);
				}
			}
		});
	}

}
