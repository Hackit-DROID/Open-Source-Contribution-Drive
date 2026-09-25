
import java.util.*;

class Student {
    int id;
    String name;
    int marks;

    Student(int id, String name, int marks) {
        this.id = id;
        this.name = name;
        this.marks = marks;
    }

    void display() {
        System.out.println(id + " | " + name + " | Marks: " + marks);
    }
}

class Marks {
    static ArrayList<Student> students = new ArrayList<>();
    static Scanner sc = new Scanner(System.in);

    static void manage() {
        System.out.print("Enter ID: ");
        int id = sc.nextInt();

        sc.nextLine();

        System.out.print("Enter Name: ");
        String name = sc.nextLine();

        System.out.print("Enter Marks: ");
        int marks = sc.nextInt();

        students.add(new Student(id, name, marks));

        System.out.println("Student Added Successfully!");

        System.out.println("\n===== STUDENT LIST =====");
        for (Student s : students) {
            s.display();
        }
    }
}

class Library {
    static void manage() {
        System.out.println("Library Module");
    }
}

class Hostel {
    static void manage() {
        System.out.println("Hostel Module");
    }
}

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        while (true) {
            System.out.println("\n===== SGGS PROJECT =====");
            System.out.println("1. Hostel");
            System.out.println("2. Library");
            System.out.println("3. Marks");
            System.out.println("4. Exit");
            System.out.print("Enter choice: ");

            int choice = sc.nextInt();

            switch (choice) {
                case 1:
                    Hostel.manage();
                    break;
                case 2:
                    Library.manage();
                    break;
                case 3:
                    Marks.manage();
                    break;
                case 4:
                    System.out.println("Exiting...");
                    return;
                default:
                    System.out.println("Invalid choice!");
            }
        }
    }
}
